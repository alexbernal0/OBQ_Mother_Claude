---
description: Scaffold a new VBT strategy file from the standard OBQ template
argument-hint: <strategy-name>
---

Scaffold a new strategy named $ARGUMENTS.

1. Create `pwb_strategies/$ARGUMENTS_vbt.py` based on the standard OBQ template structure with:
   - PARAMS dict (common defaults: leverage=1, commission=0.0002, init_cash=100_000)
   - DATASET_MAP dict
   - load_universe() function (using dl.get_pricing or dl.get_multi_ohlcv)
   - load_benchmark() function (SPX from Indices dataset)
   - compute_indicators() stub
   - compute_signals() stub
   - run_backtest() with from_order_func pattern (see vbt-patterns skill)
   - print_metrics() function
   - plot_results() stub
   - run_$ARGUMENTS() entry point

2. Create `PWB_$ARGUMENTS.ipynb` as a single-cell notebook that:
   - Adds project root to sys.path
   - Imports and calls `run_$ARGUMENTS()`

3. Add an entry for $ARGUMENTS in `knowledge/strategy_parameters.md`

Note: Use the from_order_func pattern from the vbt-patterns skill for all sizing logic.
