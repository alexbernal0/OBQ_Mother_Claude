---
name: test-generator
description: "OBQ test generation patterns — pytest structure for quantitative finance code, data validation tests, VBT backtest regression tests, and MotherDuck schema tests. Use when adding tests to any OBQ project."
---

## OBQ Test Structure

```
project/
├── tests/
│   ├── unit/           # Pure function tests (no external deps)
│   ├── integration/    # Tests with MotherDuck or external data
│   └── e2e/            # Full pipeline tests
├── conftest.py         # Shared fixtures
└── pytest.ini
```

## Standard conftest.py

```python
# conftest.py
import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_close_wide():
    """Wide-format close price DataFrame for testing."""
    dates = pd.date_range("2020-01-01", periods=252, freq="B")
    symbols = ["AAPL", "MSFT", "GOOG"]
    np.random.seed(42)
    prices = pd.DataFrame(
        100 * np.exp(np.cumsum(np.random.randn(252, 3) * 0.01, axis=0)),
        index=dates, columns=symbols
    )
    return prices

@pytest.fixture
def sample_close_long(sample_close_wide):
    """Long-format close price DataFrame for testing."""
    df = sample_close_wide.stack().reset_index()
    df.columns = ["Date", "Symbol", "adjusted_close"]
    return df

@pytest.fixture
def mock_motherduck(monkeypatch):
    """Mock MotherDuck connection for unit tests."""
    import duckdb
    conn = duckdb.connect(":memory:")
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "test_token")
    return conn
```

## Data Quality Tests

```python
# tests/unit/test_data_quality.py
import pytest
import pandas as pd
import numpy as np

class TestOHLCVValidation:
    def test_no_negative_prices(self, sample_close_wide):
        assert (sample_close_wide >= 0).all().all(), "Negative prices found"

    def test_high_ge_low(self, sample_ohlcv):
        assert (sample_ohlcv['high'] >= sample_ohlcv['low']).all()

    def test_no_all_nan_columns(self, sample_close_wide):
        all_nan = sample_close_wide.columns[sample_close_wide.isna().all()]
        assert len(all_nan) == 0, f"All-NaN symbols: {list(all_nan)}"

    def test_symbol_column_capital_s(self, sample_close_long):
        assert 'Symbol' in sample_close_long.columns, "Column should be 'Symbol' (capital S)"
        assert 'symbol' not in sample_close_long.columns

class TestPointInTime:
    def test_filing_date_not_future(self, fundamental_df):
        """Ensure no filing_date is in the future relative to signal date."""
        assert (fundamental_df['filing_date'] <= fundamental_df['signal_date']).all()

    def test_no_quarter_date_used(self, strategy_module_source):
        """Ensure strategy code uses filing_date not quarter_date."""
        assert 'quarter_date' not in strategy_module_source, \
            "Use filing_date not quarter_date for point-in-time joins"
```

## VBT Backtest Regression Tests

```python
# tests/integration/test_backtest_regression.py
import pytest
import numpy as np

class TestFTTClenowRegression:
    """Regression tests to detect strategy logic changes."""

    EXPECTED = {
        'cagr_min': 0.30,    # v3a minimum expected CAGR
        'cagr_max': 0.45,    # v3a maximum expected CAGR
        'sharpe_min': 1.5,
        'max_dd_max': -0.20, # MaxDD should not exceed -20%
        'n_trades_min': 700,
    }

    def test_cagr_in_range(self, backtest_results):
        cagr = backtest_results['cagr']
        assert self.EXPECTED['cagr_min'] <= cagr <= self.EXPECTED['cagr_max'], \
            f"CAGR {cagr:.1%} out of expected range"

    def test_sharpe_acceptable(self, backtest_results):
        assert backtest_results['sharpe'] >= self.EXPECTED['sharpe_min']

    def test_max_dd_acceptable(self, backtest_results):
        assert backtest_results['max_dd'] >= self.EXPECTED['max_dd_max'], \
            f"MaxDD {backtest_results['max_dd']:.1%} exceeds limit"

    def test_no_look_ahead_bias(self, signals_df):
        """Verify signals are shifted by 1 day (no look-ahead)."""
        # If signal uses today's close, entry must be tomorrow's open
        # Check that entry signal is always shifted relative to indicator signal
        raw_signal = signals_df['raw']
        entry_signal = signals_df['entry']
        # Entry should match raw signal shifted by 1
        assert (entry_signal == raw_signal.shift(1)).all(skipna=True)
```

## Schema Tests

```python
# tests/integration/test_motherduck_schema.py
import pytest
import duckdb, os

@pytest.mark.integration
class TestMotherDuckSchema:
    @pytest.fixture(autouse=True)
    def conn(self):
        token = os.getenv("MOTHERDUCK_TOKEN")
        if not token:
            pytest.skip("MOTHERDUCK_TOKEN not set")
        self.conn = duckdb.connect(f"md:?motherduck_token={token}")
        yield
        self.conn.close()

    def test_prod_table_exists(self):
        result = self.conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'main' AND table_name = 'PROD_EOD_survivorship'"
        ).fetchone()
        assert result[0] > 0, "PROD_EOD_survivorship table missing"

    def test_adjusted_close_no_negatives(self):
        result = self.conn.execute(
            "SELECT COUNT(*) FROM PROD_EODHD.main.PROD_EOD_survivorship "
            "WHERE adjusted_close < 0"
        ).fetchone()
        assert result[0] == 0, f"Found {result[0]} negative adjusted_close values"

    def test_no_future_dates(self):
        result = self.conn.execute(
            "SELECT MAX(date) FROM PROD_EODHD.main.PROD_EOD_survivorship"
        ).fetchone()
        from datetime import date
        assert result[0] <= date.today(), "Future dates found in production table"
```

## pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: marks tests requiring external connections (MotherDuck, EODHD)
    slow: marks tests that take >5 seconds
addopts = -v --tb=short -m "not integration"
```

Run integration tests explicitly:
```bash
pytest -m integration                    # MotherDuck-dependent tests
pytest tests/unit/                        # fast, no dependencies
pytest tests/ -m "not integration"        # all unit tests (CI safe)
```
