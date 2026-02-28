---
description: Guided workflow to log backtest results to knowledge/backtest_results_log.md
---

Guide Alex through logging the most recent backtest results:

1. Ask for the strategy name and version (e.g., "FTT Clenow v3a")
2. Ask for key metrics: CAGR, Sharpe, Sortino, Max Drawdown, Calmar, Volatility, Win Rate, Total Trades, date range
3. Ask for the benchmark performance (SPX total return over same period)
4. Format as a table row for `knowledge/backtest_results_log.md`
5. Write the row to the file
6. Also suggest if this result warrants a /super-save to SuperMemory (new strategy? significant improvement? important methodology finding?)

The log entry format:
`| Strategy | Date Run | Universe | Start | End | CAGR | Sharpe | Sortino | Max DD | Calmar | Vol | Benchmark |`
