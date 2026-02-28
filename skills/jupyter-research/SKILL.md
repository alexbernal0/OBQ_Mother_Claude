---
name: jupyter-research
description: "OBQ Jupyter and Hex.tech notebook patterns — single-cell architecture, research workflows, interactive analysis, and Jupyter MCP server integration. Use when working in notebooks or Hex.tech for OBQ research."
---

## OBQ Notebook Architecture

OBQ uses a **single-cell notebook pattern**: one notebook = one strategy call. The notebook
imports and calls the strategy module — all logic lives in `.py` files, not in the notebook.

```python
# Standard OBQ notebook cell (PWB_FTT_Clenow.ipynb)
import sys
sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")

from pwb_strategies.FTT_Clenow_vbt import run_ftt_clenow

results = run_ftt_clenow()
```

**Never put strategy logic in notebook cells** — it can't be tested, version-controlled cleanly,
or reused. Notebooks are launchers, `.py` files are the code.

## Hex.tech Patterns (Cloud Notebook — OBQ Standard)

Hex.tech is OBQ's cloud notebook platform. Key differences from local Jupyter:

```python
# Hex.tech: MotherDuck connection (cloud-to-cloud, fast)
import duckdb, os
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

# Hex.tech: Use requirements_hex.txt (subset of requirements.txt)
# Hex cells are independent — import statements needed in each cell
# Hex: no local file system — data must come from MotherDuck or uploaded

# Hex.tech: Interactive inputs (use Hex Input blocks, not input())
symbol = "AAPL"  # replaced by Hex Input block in production
```

## Research Workflow Pattern

```python
# 1. Load data
import duckdb, pandas as pd, numpy as np
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

df = conn.execute("""
    SELECT date, Symbol, adjusted_close
    FROM PROD_EODHD.main.PROD_EOD_survivorship
    WHERE date >= '2020-01-01'
    ORDER BY date, Symbol
""").df()

# 2. Pivot to wide format
close = df.pivot(index='date', columns='Symbol', values='adjusted_close')
close.index = pd.to_datetime(close.index)

# 3. Quick data quality check
print(f"Shape: {close.shape}")
print(f"NaN %: {close.isna().mean().mean():.1%}")
print(f"Date range: {close.index[0]} to {close.index[-1]}")
neg_prices = (close < 0).sum()
if neg_prices.any(): print(f"WARNING: Negative prices in {neg_prices[neg_prices>0].index.tolist()}")

# 4. Analysis
# ... research code ...

# 5. Log any findings
# Update knowledge/backtest_results_log.md if running a backtest
```

## Jupyter MCP Servers (Installed on This Machine)

Three Jupyter MCP servers are configured in `~/.claude/mcp_config.json`:
- `jupyter-executor` — execute notebook cells, get outputs
- `jupyter-complete` — notebook completions
- `jupyter-notebook` — notebook management

When working in notebooks with Claude Code active, Claude can directly execute cells
and read outputs — no copy-paste needed.

## Interactive Analysis Snippet Template

```python
# Standard OBQ interactive analysis header
import sys, os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# For MotherDuck work
import duckdb
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

# For PapersWBacktest work
sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")
from PWB_tools import data_loader as dl, indicators as ind, signals as sig
from PWB_tools import metrics as met, plots as plt_tools

print("Ready.")
```

## Plotting Standard

```python
# Always Plotly for OBQ visualizations
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(x=nav.index, y=nav.values, name='Strategy'))
fig.add_trace(go.Scatter(x=benchmark.index, y=benchmark.values, name='SPX'))
fig.update_layout(
    title="Strategy vs Benchmark",
    xaxis_title="Date",
    yaxis_title="NAV",
    template="plotly_dark",
    height=500,
)
fig.show()

# For production tearsheet — use Performance_Reporting module
import sys
sys.path.insert(0, r"C:\Users\admin\Desktop\OBQ_AI")  # or OBQ_TradingSystems_Vbt path
from Performance_Reporting import run_tearsheet
run_tearsheet(nav=nav, benchmark=spx_close, strategy_name="My Strategy")
```
