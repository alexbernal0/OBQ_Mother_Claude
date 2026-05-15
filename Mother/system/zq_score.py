#!/usr/bin/env python3
"""
ZQ Score Engine — Simple session quality measurement for Mother v5.

Reads OpenCode's native SQLite telemetry, computes a 4-component quality
score (Accuracy, Efficiency, Speed, Output), and writes reports.

Designed for portability across ALL projects (quant, web, ML, anything).
No domain-specific logic. Project-agnostic.

Usage:
    python zq_score.py --summary           # one-line JSON for widget
    python zq_score.py --latest            # full report for most recent session
    python zq_score.py --trend 7d          # 7-day trend
    python zq_score.py --session <ID>      # specific session
    python zq_score.py --all               # all recent sessions
"""

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────
OPENCODE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "zq_reports"
LATEST_FILE = REPORTS_DIR / "latest.json"
TREND_FILE = REPORTS_DIR / "trend.json"
SESSIONS_DIR = REPORTS_DIR / "sessions"

# ── Scoring constants ──────────────────────────────────────────────────────
SESSION_DURATION_CEILING_SEC = 7200  # 2 hours
COST_CEILING = 10.0  # $10/session reference

# ── ZQ Weights (sum = 1.00) ────────────────────────────────────────────────
W_ACCURACY = 0.30
W_EFFICIENCY = 0.30
W_SPEED = 0.25
W_OUTPUT = 0.15


@dataclass
class SessionMetrics:
    """Raw metrics from OpenCode DB."""
    session_id: str
    title: str
    directory: str = ""
    agent: str = ""
    model: str = ""
    is_subagent: bool = False
    # Time
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    # Messages
    total_messages: int = 0
    assistant_messages: int = 0
    # Tokens (from session table directly)
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_reasoning: int = 0
    cache_read: int = 0
    cache_write: int = 0
    # Cost
    total_cost: float = 0.0
    # Output
    lines_added: int = 0
    lines_deleted: int = 0
    files_changed: int = 0
    # Tool-use
    tool_calls: int = 0
    tool_errors: int = 0
    bash_repeats: int = 0
    # Models used (per-message)
    models: dict = field(default_factory=dict)


@dataclass
class ZQScore:
    """Computed ZQ score for a session."""
    session_id: str
    title: str
    zq: float = 0.0
    accuracy_score: float = 0.0
    efficiency_score: float = 0.0
    speed_score: float = 0.0
    output_score: float = 0.0
    # Derived diagnostics
    cache_hit_rate: float = 0.0
    cheap_model_ratio: float = 0.0
    cost: float = 0.0
    duration_min: float = 0.0
    grade: str = ""
    insights: list = field(default_factory=list)


def connect_db() -> Optional[sqlite3.Connection]:
    if not OPENCODE_DB.exists():
        print(f"ERROR: OpenCode DB not found at {OPENCODE_DB}", file=sys.stderr)
        return None
    conn = sqlite3.connect(str(OPENCODE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def extract_metrics(conn: sqlite3.Connection, session_id: str) -> Optional[SessionMetrics]:
    """Pull raw metrics for one session."""
    row = conn.execute("SELECT * FROM session WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return None

    m = SessionMetrics(
        session_id=session_id,
        title=row["title"] or "(untitled)",
        directory=row["directory"] or "",
        agent=row["agent"] or "",
        model=row["model"] or "",
        is_subagent=row["parent_id"] is not None,
        lines_added=row["summary_additions"] or 0,
        lines_deleted=row["summary_deletions"] or 0,
        files_changed=row["summary_files"] or 0,
        total_cost=row["cost"] or 0.0,
        tokens_input=row["tokens_input"] or 0,
        tokens_output=row["tokens_output"] or 0,
        tokens_reasoning=row["tokens_reasoning"] or 0,
        cache_read=row["tokens_cache_read"] or 0,
        cache_write=row["tokens_cache_write"] or 0,
    )

    # Timestamps
    created = row["time_created"]
    updated = row["time_updated"]
    if created and updated:
        m.duration_seconds = (updated - created) / 1000.0
        m.started_at = datetime.fromtimestamp(created / 1000).isoformat()
        m.ended_at = datetime.fromtimestamp(updated / 1000).isoformat()

    # Message count
    msg_rows = conn.execute(
        "SELECT data FROM message WHERE session_id = ?", (session_id,)
    ).fetchall()
    m.total_messages = len(msg_rows)

    for msg in msg_rows:
        try:
            data = json.loads(msg["data"])
        except (json.JSONDecodeError, TypeError):
            continue
        if data.get("role") == "assistant":
            m.assistant_messages += 1
            model_id = data.get("modelID", "unknown")
            m.models[model_id] = m.models.get(model_id, 0) + 1

    # Tool calls + errors + bash repeats from part table
    try:
        tool_parts = conn.execute(
            "SELECT data FROM part WHERE session_id = ? AND json_extract(data,'$.type')='tool'",
            (session_id,)
        ).fetchall()
        bash_seen: dict = {}
        for tp in tool_parts:
            try:
                td = json.loads(tp["data"])
            except (json.JSONDecodeError, TypeError):
                continue
            m.tool_calls += 1
            state = td.get("state") or {}
            if state.get("status") == "error":
                m.tool_errors += 1
            # Detect bash repeats
            if td.get("tool") == "bash":
                cmd = (state.get("input") or {}).get("command", "")
                if cmd:
                    bash_seen[cmd] = bash_seen.get(cmd, 0) + 1
        m.bash_repeats = sum(c - 1 for c in bash_seen.values() if c > 1)
    except sqlite3.Error:
        pass

    return m


def compute_zq(m: SessionMetrics) -> ZQScore:
    """Compute the 4-component ZQ score."""
    s = ZQScore(session_id=m.session_id, title=m.title, cost=m.total_cost)
    s.duration_min = round(m.duration_seconds / 60.0, 1)

    # ── ACCURACY (30%) ─────────────────────────────────────────────────────
    # Lower error rate and lower repeat rate = higher accuracy.
    if m.tool_calls > 0:
        err_rate = m.tool_errors / m.tool_calls
        repeat_rate = m.bash_repeats / max(1, m.tool_calls)
        # Error penalty: 0% → 1.0, 5% → 0.6, 10%+ → 0.2
        err_score = max(0.0, 1.0 - (err_rate * 8.0))
        # Repeat penalty: <2% → 1.0, 5% → 0.7, 10%+ → 0.4
        rep_score = max(0.0, 1.0 - (repeat_rate * 6.0))
        s.accuracy_score = round((err_score + rep_score) / 2.0, 3)
    else:
        s.accuracy_score = 0.8  # neutral when no tool data

    # ── EFFICIENCY (30%) ───────────────────────────────────────────────────
    # Cache hit rate + cheap-model routing.
    total_tokens = m.tokens_input + m.tokens_output + m.cache_read + m.cache_write
    if total_tokens > 0:
        s.cache_hit_rate = m.cache_read / total_tokens
        # 50% → 0.0, 95% → 1.0
        cache_score = min(1.0, max(0.0, (s.cache_hit_rate - 0.5) / 0.45))
    else:
        cache_score = 0.5

    # Cheap-model routing
    total_msgs = sum(m.models.values()) if m.models else 0
    if total_msgs > 0:
        cheap = sum(c for mod, c in m.models.items()
                    if any(k in mod.lower() for k in ["haiku", "mini", "flash", "devstral"]))
        mid = sum(c for mod, c in m.models.items() if "sonnet" in mod.lower() or "grok" in mod.lower())
        s.cheap_model_ratio = (cheap + 0.6 * mid) / total_msgs
        routing_score = min(1.0, s.cheap_model_ratio / 0.7)
    else:
        routing_score = 0.5

    # Blend: 60% cache, 40% routing
    s.efficiency_score = round(0.6 * cache_score + 0.4 * routing_score, 3)

    # ── SPEED (25%) ────────────────────────────────────────────────────────
    # Shorter duration = higher score. Penalize message bloat.
    duration_score = 1.0 - min(1.0, m.duration_seconds / SESSION_DURATION_CEILING_SEC)
    # Message efficiency: lower messages-per-output-token = better
    if m.tokens_output > 0 and m.assistant_messages > 0:
        # Healthy: roughly 500-2000 tokens per assistant message
        tpm = m.tokens_output / m.assistant_messages
        if tpm < 100:
            msg_score = 0.5  # too chatty
        elif tpm < 500:
            msg_score = 0.8
        else:
            msg_score = 1.0
    else:
        msg_score = 0.5

    # Bloat penalty
    bloat_mult = 1.0
    if m.total_messages > 200:
        bloat_mult = 0.6
    elif m.total_messages > 100:
        bloat_mult = 0.8

    s.speed_score = round((0.6 * duration_score + 0.4 * msg_score) * bloat_mult, 3)

    # ── OUTPUT (15%) ───────────────────────────────────────────────────────
    # Did this session produce ANY tangible deliverable?
    has_code = (m.lines_added + m.lines_deleted) > 0
    has_files = m.files_changed > 0
    has_research = m.assistant_messages >= 5 and m.tokens_output > 5000

    if has_code or has_files:
        s.output_score = 1.0
    elif has_research:
        s.output_score = 0.7  # research/exploration credit
    elif m.assistant_messages > 0:
        s.output_score = 0.4
    else:
        s.output_score = 0.0

    # ── WEIGHTED ZQ ────────────────────────────────────────────────────────
    s.zq = round(
        W_ACCURACY * s.accuracy_score +
        W_EFFICIENCY * s.efficiency_score +
        W_SPEED * s.speed_score +
        W_OUTPUT * s.output_score,
        3
    )
    s.zq = round(min(1.0, max(0.0, s.zq)), 3)

    # Grade
    if s.zq >= 0.85:
        s.grade = "A"
    elif s.zq >= 0.70:
        s.grade = "B"
    elif s.zq >= 0.55:
        s.grade = "C"
    elif s.zq >= 0.40:
        s.grade = "D"
    else:
        s.grade = "F"

    # ── INSIGHTS ───────────────────────────────────────────────────────────
    if s.cache_hit_rate < 0.5 and total_tokens > 5000:
        s.insights.append(f"Low cache hit rate ({s.cache_hit_rate:.0%}) — prompt caching may not be active")
    elif s.cache_hit_rate > 0.85:
        s.insights.append(f"Excellent cache efficiency ({s.cache_hit_rate:.0%})")

    if m.tool_calls > 20 and m.tool_errors / max(1, m.tool_calls) > 0.10:
        s.insights.append(f"High tool error rate ({m.tool_errors}/{m.tool_calls}) — check tool arguments")

    if m.bash_repeats > 3:
        s.insights.append(f"Bash repeat waste ({m.bash_repeats} duplicates) — cache results or take notes")

    if m.total_cost > 5.0:
        s.insights.append(f"High session cost (${m.total_cost:.2f}) — consider downtiering model")

    if m.total_messages > 200:
        s.insights.append(f"Heavy session ({m.total_messages} messages) — start /handoff earlier next time")

    if s.cheap_model_ratio < 0.3 and total_msgs > 10:
        s.insights.append(f"Heavy reliance on expensive models ({s.cheap_model_ratio:.0%} cheap) — review routing")

    if s.output_score < 0.5 and m.assistant_messages > 20:
        s.insights.append("Long session with low tangible output — verify deliverable")

    return s


def get_recent_sessions(conn: sqlite3.Connection, days: int = 30, root_only: bool = True) -> list[str]:
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    where = "time_created > ? AND time_archived IS NULL"
    if root_only:
        where += " AND parent_id IS NULL"
    rows = conn.execute(
        f"SELECT id FROM session WHERE {where} ORDER BY time_created DESC", (cutoff,)
    ).fetchall()
    return [r["id"] for r in rows]


def save_report(score: ZQScore, metrics: SessionMetrics) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "score": asdict(score),
        "metrics": asdict(metrics),
        "generated_at": datetime.now().isoformat(),
    }
    LATEST_FILE.write_text(json.dumps(report, indent=2))
    (SESSIONS_DIR / f"{score.session_id}.json").write_text(json.dumps(report, indent=2))


def compute_trend(scores: list[ZQScore]) -> dict:
    if not scores:
        return {"sessions": 0, "average_zq": 0.0, "trend": "no_data"}
    zqs = [s.zq for s in scores]
    avg = round(sum(zqs) / len(zqs), 3)
    mid = len(zqs) // 2
    if mid > 0:
        first_half = sum(zqs[mid:]) / max(1, len(zqs) - mid)  # older
        second_half = sum(zqs[:mid]) / max(1, mid)  # newer
        delta = round(second_half - first_half, 3)
        if delta > 0.02:
            direction = "improving"
        elif delta < -0.02:
            direction = "declining"
        else:
            direction = "stable"
    else:
        direction = "insufficient_data"
        delta = 0.0
    return {
        "sessions": len(scores),
        "average_zq": avg,
        "trend": direction,
        "delta": delta,
        "best": round(max(zqs), 3),
        "worst": round(min(zqs), 3),
    }


def format_summary(score: ZQScore, trend: Optional[dict] = None) -> dict:
    """One-line JSON for widget consumption."""
    return {
        "zq": score.zq,
        "grade": score.grade,
        "accuracy": score.accuracy_score,
        "efficiency": score.efficiency_score,
        "speed": score.speed_score,
        "output": score.output_score,
        "trend_direction": (trend or {}).get("trend", "n/a"),
        "trend_delta": (trend or {}).get("delta", 0.0),
        "session_id": score.session_id[:8],
        "generated_at": datetime.now().isoformat(),
    }


def print_full_report(score: ZQScore, metrics: SessionMetrics) -> None:
    bar = "=" * 60
    sep = "-" * 60
    print(f"\n{bar}")
    print(f"  ZQ Score: {score.zq}  Grade: {score.grade}")
    print(f"  Session: {score.title[:50]}")
    print(f"  ID: {score.session_id}")
    print(bar)
    print(f"  Accuracy:   {score.accuracy_score:.3f}  (weight 30%)")
    print(f"  Efficiency: {score.efficiency_score:.3f}  (weight 30%)")
    print(f"  Speed:      {score.speed_score:.3f}  (weight 25%)")
    print(f"  Output:     {score.output_score:.3f}  (weight 15%)")
    print(sep)
    print(f"  Cost: ${score.cost:.4f}   Duration: {score.duration_min} min")
    print(f"  Cache hit rate: {score.cache_hit_rate:.1%}")
    print(f"  Cheap-model ratio: {score.cheap_model_ratio:.1%}")
    print(f"  Messages: {metrics.total_messages} ({metrics.assistant_messages} assistant)")
    print(f"  Tool calls: {metrics.tool_calls}  errors: {metrics.tool_errors}")
    print(f"  Lines: +{metrics.lines_added} -{metrics.lines_deleted}  Files: {metrics.files_changed}")
    if score.insights:
        print(sep)
        print("  Insights:")
        for ins in score.insights:
            print(f"    * {ins}")
    print(f"{bar}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="ZQ Score — Mother v5 session quality metric")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--summary", action="store_true", help="One-line JSON (for widget)")
    group.add_argument("--latest", action="store_true", help="Full report for most recent session")
    group.add_argument("--session", metavar="ID", help="Specific session ID")
    group.add_argument("--trend", metavar="WINDOW", help="Trend report (e.g., 7d, 30d)")
    group.add_argument("--all", action="store_true", help="Score all recent sessions")
    args = parser.parse_args()

    if not any([args.summary, args.latest, args.session, args.trend, args.all]):
        args.summary = True  # default

    conn = connect_db()
    if not conn:
        return 1

    try:
        if args.session:
            metrics = extract_metrics(conn, args.session)
            if not metrics:
                print(f"Session {args.session} not found", file=sys.stderr)
                return 1
            score = compute_zq(metrics)
            save_report(score, metrics)
            print_full_report(score, metrics)
            return 0

        if args.trend:
            days = int(args.trend.rstrip("d").rstrip("D")) if args.trend.lower().endswith("d") else int(args.trend)
            ids = get_recent_sessions(conn, days=days, root_only=True)
            scores = []
            for sid in ids:
                m = extract_metrics(conn, sid)
                if m:
                    scores.append(compute_zq(m))
            trend = compute_trend(scores)
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            TREND_FILE.write_text(json.dumps(trend, indent=2))
            print(json.dumps(trend, indent=2))
            return 0

        if args.all:
            ids = get_recent_sessions(conn, days=30, root_only=True)
            results = []
            for sid in ids[:50]:  # cap at 50
                m = extract_metrics(conn, sid)
                if m:
                    s = compute_zq(m)
                    save_report(s, m)
                    results.append({"id": sid[:8], "zq": s.zq, "grade": s.grade, "title": s.title[:50]})
            print(json.dumps(results, indent=2))
            return 0

        # --latest or --summary
        ids = get_recent_sessions(conn, days=30, root_only=True)
        if not ids:
            print(json.dumps({"error": "No recent sessions found"}))
            return 1

        latest_id = ids[0]
        metrics = extract_metrics(conn, latest_id)
        if not metrics:
            print(json.dumps({"error": f"Failed to extract metrics for {latest_id}"}))
            return 1

        score = compute_zq(metrics)
        save_report(score, metrics)

        # Compute 7d trend for context
        recent = ids[:20]  # last 20 sessions for trend
        trend_scores = []
        for sid in recent:
            tm = extract_metrics(conn, sid)
            if tm:
                trend_scores.append(compute_zq(tm))
        trend = compute_trend(trend_scores)
        TREND_FILE.write_text(json.dumps(trend, indent=2))

        if args.summary:
            print(json.dumps(format_summary(score, trend)))
        else:
            print_full_report(score, metrics)
            print(f"  7-day trend: {trend['trend']}  (avg: {trend['average_zq']}, delta: {trend['delta']:+.3f})")
            print()

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
