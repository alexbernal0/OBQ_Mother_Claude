---
name: streamlit-skills
description: "Streamlit production patterns for GoldenOpp-style multi-page apps: caching (cache_data vs cache_resource), session_state cross-page sharing, chat components with streaming, data_editor save patterns, CSS injection, st.fragment partial reruns, Streamlit Cloud deployment gotchas. Sources: streamlit/streamlit, streamlit/cookbook, MarcSkovMadsen/awesome-streamlit. Use when building or debugging any Streamlit page in GoldenOpp or OBQ apps."
compatibility: "Claude Code (VSCode + CLI), OpenCode"
metadata:
  author: OBQ
  source: "streamlit/streamlit docs v1.55, streamlit/cookbook, MarcSkovMadsen/awesome-streamlit"
  updated: "2026-03-28"
  version: "1.0"
  allowed-tools: "Read, Bash, Edit, Write"
---

# STREAMLIT SKILLS — GoldenOpp Production Patterns

**Sources analyzed:**
- https://github.com/streamlit/streamlit (v1.55.0 docs + source)
- https://github.com/streamlit/cookbook
- https://github.com/MarcSkovMadsen/awesome-streamlit

---

## 1. CACHING — DECISION TREE

```
Return serializable data (DataFrame, dict, str)?  → @st.cache_data
Return unserializable object (DB connection, model)? → @st.cache_resource
```

**Rule:** `cache_data` creates a copy per user (safe, slower for huge data). `cache_resource` is a singleton shared across ALL users (fast, mutation-dangerous).

```python
# ✅ CORRECT: DB queries → cache_data with TTL
@st.cache_data(ttl=3600, show_spinner="Loading...")
def query_db(_conn, sql: str) -> pd.DataFrame:   # _conn = not hashed (underscore prefix)
    return _conn.execute(sql).df()

# ✅ CORRECT: DB connection → cache_resource (singleton, not copied)
@st.cache_resource
def get_connection(token: str):
    import duckdb
    con = duckdb.connect(f"md:?motherduck_token={token}")
    con.execute("USE golden_opp")
    return con

# ❌ WRONG: Using cache_data for a connection (will fail to pickle)
@st.cache_data
def bad_connection(): return duckdb.connect(...)

# ✅ CORRECT: Unhashable param → prefix with underscore
@st.cache_data(ttl=300)
def load_portfolio(_con, tickers: tuple) -> pd.DataFrame:  # _con skipped in hash
    ...
```

**TTL shortcuts:** `ttl=300` (5min), `ttl=3600` (1hr), `ttl=86400` (1day), `ttl="1d"` (string also works in v1.37+)

**Force invalidate cache:** `st.cache_data.clear()` — use after a save operation.

---

## 2. SESSION STATE — CROSS-PAGE PATTERNS

Session state IS shared across all pages automatically. Keys set on page A are available on page B.

```python
# ── Initializing defaults (do ONCE at top of each page) ──────────────────
def _init():
    defaults = {
        "authenticated": False,
        "current_mode":  "simple",
        "chat_history":  [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()  # Safe to call multiple times — only sets missing keys

# ── Auth guard pattern (every page except home) ──────────────────────────
if not st.session_state.get("authenticated"):
    st.error("🔒 Please log in first.")
    st.stop()  # ← STOP here, nothing below executes

# ── Persisting edited data before navigation ─────────────────────────────
def _save_before_leave():
    # Call before st.rerun() to avoid losing edits
    st.session_state["pending_save"] = st.session_state.get("editor_data")
```

**Gotcha:** `st.rerun()` reruns the entire script. Any local variables are lost. Only `st.session_state` persists.

---

## 3. MULTI-PAGE APP — PAGES/ DIRECTORY

Our GoldenOpp uses the `pages/` folder approach (not `st.navigation`).

```
streamlit_app/
├── app.py              ← entrypoint (password + home chat)
├── pages/
│   ├── 1_Data_Sync.py
│   ├── 2_Screener.py
│   ├── 3_Analyst.py
│   └── ...
```

**Rules:**
- Files in `pages/` are auto-discovered, sorted by filename prefix number
- Emoji in filename: `1_🔄_Data_Sync.py` → shows emoji in sidebar
- `set_page_config` works in EACH page file independently
- Shared state via `st.session_state` — no import needed

**Path imports from sibling/parent directories (Streamlit Cloud):**

```python
# In streamlit_app/pages/6_Options_Expert.py
import sys
from pathlib import Path

_app_dir = Path(__file__).resolve().parent.parent   # → streamlit_app/
_opt_dir = _app_dir.parent / "Option_Enhancements_v2"

for p in [str(_opt_dir), str(_app_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Now imports from both directories work:
from session_manager import create_session  # from Option_Enhancements_v2/
from screener_engine import load_universe   # from streamlit_app/
```

**Streamlit Cloud path gotcha:** On Cloud, repo is at `/mount/src/repo_name/`. Relative imports must use `Path(__file__).resolve()` not `os.getcwd()`.

---

## 4. CHAT COMPONENTS — STREAMING PATTERNS

**v1.55 key fact:** `st.chat_input` now natively supports `accept_file=True` and `accept_audio=True` — no need for separate `st.file_uploader`!

```python
# ── NEW v1.55: Built-in file attachment in chat input ───────────────────
prompt = st.chat_input(
    "Ask anything...",
    accept_file=True,          # allow file uploads
    file_type=["png","jpg","pdf"],
    max_upload_size=10,        # MB
)
if prompt:
    user_text  = prompt.text   # str
    user_files = prompt.files  # list[UploadedFile], empty if no files

# ── OLD pattern (still works) ────────────────────────────────────────────
col1, col2 = st.columns([1, 9])
uploaded = col1.file_uploader("📎", type=["png","jpg"], label_visibility="collapsed")
user_input = col2.chat_input("Ask...")

# ── Streaming Claude response ─────────────────────────────────────────────
with st.chat_message("assistant"):
    response_box = st.empty()
    full_text = ""
    with client.messages.stream(...) as stream:
        for chunk in stream.text_stream:
            full_text += chunk
            response_box.markdown(full_text + "▌")  # ▌ = cursor effect
    response_box.markdown(full_text)  # final, no cursor

# ── Auto-scroll to latest message ────────────────────────────────────────
# Option A: st.container(height=N) — scrollable, newest at bottom naturally
chat_box = st.container(height=480)
with chat_box:
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Option B: JS injection for programmatic scroll
import streamlit.components.v1 as components
components.html("""
<script>
    var chats = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
    if(chats.length) chats[chats.length-1].scrollIntoView({behavior:'smooth'});
</script>
""", height=0)
```

**Chat pattern — key decision:**
- `st.chat_input` at PAGE level → pinned to bottom of full page
- `st.chat_input` inside `with st.sidebar:` or `with container:` → inline, not pinned
- Use `st.container(height=N)` + `with container: st.chat_message(...)` for fixed-height scrollable chat

---

## 5. DATA EDITOR — SAVE PATTERN

```python
# ── Editable table with save button ──────────────────────────────────────
df = load_data_from_db(tok)

edited = st.data_editor(
    df,
    num_rows="dynamic",        # allow adding/deleting rows
    use_container_width=True,
    column_config={
        "price": st.column_config.NumberColumn("Price", format="$%.2f"),
        "ticker": st.column_config.TextColumn("Ticker", width="small"),
        "active": st.column_config.CheckboxColumn("Active"),
        "link": st.column_config.LinkColumn("URL"),
        "img": st.column_config.ImageColumn("Preview"),
    },
    key="my_editor",
    hide_index=True,
)

# Save only when button clicked (not on every edit)
if st.button("💾 Save"):
    save_to_db(tok, edited)
    st.cache_data.clear()     # invalidate cache so fresh data loads
    st.rerun()

# ── Access edits via session_state ────────────────────────────────────────
# After each rerun, st.session_state["my_editor"] contains:
# {"edited_rows": {0: {"col": new_val}}, "added_rows": [...], "deleted_rows": [...]}
edits = st.session_state.get("my_editor", {})
```

---

## 6. CSS INJECTION — CUSTOM STYLING

```python
# ── Taller chat input (3× default) ───────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stChatInput"] textarea {
        min-height: 120px !important;
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Color-code dataframe cells ────────────────────────────────────────────
def _color_rank(val):
    try:
        n = float(val)
        if n >= 70: return "background-color: #0e2e0e; color: #6fcf6f"
        if n >= 50: return "background-color: #1e1e0e; color: #c4c470"
        return "background-color: #2e0e0e; color: #f07070"
    except: return ""

styled = df.style.applymap(_color_rank, subset=["score_col"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Hide sidebar nav, default padding, etc. ───────────────────────────────
st.markdown("""
<style>
    /* Hide default hamburger menu */
    [data-testid="stSidebarNav"] { display: none; }
    /* Remove top padding */
    .block-container { padding-top: 1rem; }
    /* Full-width main content */
    .main .block-container { max-width: 100%; }
</style>
""", unsafe_allow_html=True)

# ── Dark/light mode adaptive colors ──────────────────────────────────────
# Use st.chat_message(), st.metric(), st.info() etc. — they adapt automatically
# AVOID hardcoded hex colors (#1a1a2e) in chat messages — use st.chat_message() instead
```

---

## 7. ST.FRAGMENT — PARTIAL RERUNS (v1.37+)

`@st.fragment` runs only that section on interaction, NOT the full page. Critical for performance in complex pages.

```python
# ── Fragment: only this section reruns when button clicked ───────────────
@st.fragment
def portfolio_chat_section():
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt := st.chat_input("Ask..."):
        st.session_state["messages"].append({"role":"user","content":prompt})
        # response generation here
        st.rerun(scope="fragment")  # only reruns THIS fragment

portfolio_chat_section()

# ── Fragment with interval polling ───────────────────────────────────────
@st.fragment(run_every="30s")   # auto-refresh every 30 seconds
def live_prices():
    prices = fetch_prices()
    st.dataframe(prices)

live_prices()
```

**When to use fragment:** Any section that has its own interactive elements (chat, charts, forms) AND shouldn't trigger full page reruns.

---

## 8. LAYOUT PATTERNS

```python
# ── Standard 2-col layout: main + right sidebar ──────────────────────────
main_col, side_col = st.columns([3, 1])
with main_col:
    ...  # main content
with side_col:
    ...  # session history, filters, etc.

# ── Metric row ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Label", "Value", delta="+1.2%", delta_color="normal")
c2.metric("Label", "Value", delta="-0.5%", delta_color="inverse")  # red for negative good

# ── Tabs (don't cause full rerun) ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Valuation", "Quality", "Momentum"])
with tab1: ...
with tab2: ...

# ── Fixed-height scrollable container ────────────────────────────────────
chat_box = st.container(height=480)
with chat_box:
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Sessions")
    # sidebar content here

# ── Popover (v1.32+) — great for inline settings/menus ───────────────────
with st.popover("⚙️ Settings"):
    mode = st.selectbox("Mode", ["simple", "professional"])
```

---

## 9. PERFORMANCE GOTCHAS

```python
# ── AVOID: calling st.rerun() in a loop ──────────────────────────────────
# BAD: infinite loop
while True:
    data = fetch()
    st.write(data)
    time.sleep(5)
    st.rerun()  # ← endless loop

# GOOD: use @st.fragment(run_every="5s") instead

# ── AVOID: heavy computation without caching ─────────────────────────────
# BAD: runs on EVERY user interaction
df = pd.read_csv("big_file.csv")  # ← no cache

# GOOD:
@st.cache_data(ttl=3600)
def load_data(): return pd.read_csv("big_file.csv")

# ── AVOID: creating DB connections in the body ───────────────────────────
# BAD: new connection every rerun
con = duckdb.connect("md:?token=...")  # ← runs every interaction

# GOOD: use cache_resource for the connection singleton
@st.cache_resource
def get_con(): return duckdb.connect("md:?token=...")

# ── Early exit with st.stop() ────────────────────────────────────────────
if not authenticated:
    show_login()
    st.stop()  # ← nothing below runs; cleaner than if/else nesting

# ── Session state as guard against re-loading ────────────────────────────
if "portfolio_brief" not in st.session_state:
    st.session_state["portfolio_brief"] = build_brief(tok)
brief = st.session_state["portfolio_brief"]  # always uses cached session version
```

---

## 10. STREAMLIT CLOUD DEPLOYMENT

**Secrets:**
```toml
# .streamlit/secrets.toml (local dev)
MOTHERDUCK_TOKEN = "eyJ..."
ANTHROPIC_API_KEY = "sk-ant-..."
APP_PASSWORD = "hunter2"

# Access:
token = st.secrets["MOTHERDUCK_TOKEN"]
# or via env var: os.getenv("MOTHERDUCK_TOKEN")
```

**Requirements pitfall:** Streamlit Cloud uses `streamlit_app/requirements.txt` if the entrypoint is in a subfolder.

```
# streamlit_app/requirements.txt
streamlit        # no version pin = latest
anthropic
duckdb>=0.10.0
pandas
yfinance
fpdf2
```

**Import path on Cloud:**
- Repo root: `/mount/src/repo_name/`
- Entrypoint: `/mount/src/repo_name/streamlit_app/app.py`
- Always use `Path(__file__).resolve()` for paths, never `os.getcwd()`

**Redeployment trigger:** Any push to the connected branch triggers auto-redeploy. `.streamlit/config.toml` changes also trigger redeploy.

**Memory limits on free tier:** 1GB RAM. Keep `@st.cache_data` entries bounded with `max_entries=50`.

---

## 11. COMPONENT LIBRARY TIPS (from awesome-streamlit)

```python
# ── st.write_stream for streaming text (v1.31+) ───────────────────────────
def stream_response():
    for word in ["hello", " world"]:
        yield word
        time.sleep(0.1)

st.write_stream(stream_response())  # shows streaming text natively

# ── st.status for long operations ────────────────────────────────────────
with st.status("Processing...") as status:
    do_step_1()
    st.write("Step 1 done")
    do_step_2()
    status.update(label="Complete!", state="complete")

# ── st.toast for non-blocking notifications ──────────────────────────────
st.toast("✅ Saved successfully!", icon="✅")

# ── st.link_button for prominent external links ──────────────────────────
st.link_button("View on GitHub", "https://github.com/alexbernal0/OBQ_GoldenOpp")

# ── image display in chat ────────────────────────────────────────────────
if msg.get("image_b64"):
    st.image(f"data:image/png;base64,{msg['image_b64']}", width=300)
```

---

## 12. GOLDENOPP-SPECIFIC PATTERNS

Based on observed bugs and fixes in the actual app:

```python
# ── Cross-directory import (pages/ → Option_Enhancements_v2/) ────────────
_opt_dir = Path(__file__).resolve().parent.parent.parent / "Option_Enhancements_v2"
if str(_opt_dir) not in sys.path:
    sys.path.insert(0, str(_opt_dir))

# ── Resilient imports with fallback stubs ────────────────────────────────
try:
    from session_manager import create_session
except ImportError:
    def create_session(tok, **kw): return {"id": "local", "messages": []}

# ── TypeError-safe function calls (version mismatch) ─────────────────────
try:
    sess = create_session(tok, name="...", source_page="portfolio")
except TypeError:
    sess = create_session(tok, name="...")  # old signature fallback

# ── DuckDB with MotherDuck — always USE golden_opp ───────────────────────
@st.cache_resource
def get_md_conn(token: str):
    import duckdb
    con = duckdb.connect(f"md:?motherduck_token={token}")
    con.execute("USE golden_opp")
    return con

# ── Pandas Styler in st.dataframe — light/dark safe approach ─────────────
# DON'T hardcode dark bg colors — use green/amber/red which work in both modes
def _color(val):
    try:
        n = float(val)
        if n >= 70: return "background-color: #4caf50; color: white"   # always readable
        if n >= 50: return "background-color: #ff9800; color: white"
        return "background-color: #f44336; color: white"
    except: return ""

# ── st.selectbox returning string not index ──────────────────────────────
# COMMON BUG: treating selectbox return as index
options = [("Label A", "val_a"), ("Label B", "val_b")]
labels  = [o[0] for o in options]
chosen_label = st.selectbox("Pick", labels)
idx    = labels.index(chosen_label)  # ← convert back to index
chosen = options[idx][1]             # ← get the value
```

---

## QUICK REFERENCE — API SIGNATURES

```python
# Caching
@st.cache_data(ttl=3600, show_spinner=False, max_entries=100)
@st.cache_resource
st.cache_data.clear()

# Chat
st.chat_message("user" | "assistant" | custom_avatar)
st.chat_input(placeholder, accept_file=False|True|"multiple", file_type=[...], key=...)

# Layout
st.columns([1,2,3])                   # width ratio list
st.container(height=480, border=True)
st.tabs(["Tab 1", "Tab 2"])
st.expander("Label", expanded=False)
st.popover("Label")
st.sidebar

# Data
st.dataframe(df, use_container_width=True, hide_index=True, height=400)
st.data_editor(df, num_rows="dynamic", column_config={...}, key="editor")

# Status
st.spinner("Loading...")
st.status("Processing...", expanded=True)
st.toast("Message", icon="✅")
st.stop()  # halt execution

# Components
import streamlit.components.v1 as components
components.html("<script>...</script>", height=0)
```
