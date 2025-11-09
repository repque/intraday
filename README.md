# Intraday Trading System

A Python-based algorithmic trading framework for backtesting and executing intraday trading strategies on stocks and ETFs.

## Overview

This framework enables traders to:
- Develop and backtest algorithmic trading strategies using historical intraday data
- Execute automated trading strategies in live mode with real-time market data
- Track profit & loss (P&L), positions, and commissions
- Generate interactive performance charts
- Run multiple strategies concurrently across different symbols

## Features

### Strategy Configuration
- **Flexible Entry Rules**: Define when to enter positions
  - Initial breakout detection based on price action
  - Time-based entries at specific hours/minutes
  - Composite conditions with AND logic
- **Risk Management Exit Rules**: Control when to exit positions
  - Stop loss (percentage-based)
  - Take profit (percentage-based)
  - Time-based exits (end-of-day or specific times)
- **Built-in Safety Controls**:
  - Automatic end-of-day position closing (15:59)
  - Trading hours filtering (9:30 AM - 4:00 PM)
  - Cash availability validation
  - Round lot enforcement (multiples of 10 shares)

### Backtesting
- Single-day or multi-day backtesting against historical CSV data
- Configurable starting capital and commission rates
- Detailed P&L tracking (realized and unrealized)
- Interactive HTML charts with Plotly showing:
  - Price action
  - Buy/sell markers
  - Performance metrics

### Live Trading
- Real-time data integration (requires implementation in `custom.py`)
- Broker API integration for order execution (requires implementation in `custom.py`)
- Live data recording to CSV for future backtesting

## Installation

### Requirements
- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/repque/intraday.git
cd intraday

# Create virtual environment and install dependencies
uv sync --no-install-project

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# Or on Windows: .venv\Scripts\activate
```

### Alternative Setup with pip

```bash
git clone https://github.com/repque/intraday.git
cd intraday

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# Or on Windows: .venv\Scripts\activate

# Install dependencies
pip install pandas plotly six
```

## Usage

### Quick Start

Run the default configuration:
```bash
python app.py
```

This runs a backtest using the example strategy in `app.py` against the sample data in `data/IVV.csv`.

### Basic Example

```python
from core import Config
from coroutines import initial_breakout, time_based, stop_loss, stop_profit
from app import run
import datetime

# Define a trading strategy
config = Config(
    symbol='IVV',
    equity_pct=0.50,  # Use 50% of available equity per trade
    entry_rules=[
        initial_breakout(45)  # Enter on breakout after 45-minute observation period
    ],
    exit_rules=[
        time_based(14, 15),    # Exit at 2:15 PM
        stop_loss(0.02),       # Exit if position loses 2%
        stop_profit(0.02)      # Exit if position gains 2%
    ]
)

# Run backtest
run(
    configs=[config],
    live=False,
    cash=25000,
    commission=0,
    save_charts=True
)
```

### Running Multiple Strategies

```python
# Define multiple strategies for different symbols or parameters
config1 = Config(
    symbol='IVV',
    equity_pct=0.50,
    entry_rules=[initial_breakout(45)],
    exit_rules=[time_based(14, 15), stop_loss(0.02), stop_profit(0.02)]
)

config2 = Config(
    symbol='SPY',
    equity_pct=0.30,
    entry_rules=[initial_breakout(30)],
    exit_rules=[stop_loss(0.01), stop_profit(0.03)]
)

# Run all strategies together
run(configs=[config1, config2], live=False, save_charts=True)
```

### Backtesting Specific Dates

```python
# Test against a specific day
run(
    configs=[config],
    live=False,
    specific_day=datetime.datetime(2020, 4, 2),
    save_charts=True
)

# Process all dates in CSV data, day by day
from app import run_dates
run_dates(configs=[config], save_charts=True)
```

### Live Trading

```python
# Run in live mode (requires broker integration in custom.py)
run(
    configs=[config],
    live=True,
    cash=25000,
    commission=0.005,  # $0.005 per share
    interval=1,  # Poll every 1 minute
    save_charts=True
)
```

## Available Entry Rules

### `initial_breakout(period_length, repeat=False)`
Generates a buy signal when price breaks above the maximum price observed during the initial period.

**Parameters:**
- `period_length` (int): Number of minutes to observe before detecting breakout (e.g., 45)
- `repeat` (bool): Allow multiple signals per day (default: False)

**Example:**
```python
entry_rules=[initial_breakout(45)]  # Enter on breakout after 45-minute high
```

### `time_based(hour, minute)`
Generates a signal at a specific time of day.

**Parameters:**
- `hour` (int): Hour in 24-hour format (0-23)
- `minute` (int): Minute (0-59)

**Example:**
```python
entry_rules=[time_based(10, 30)]  # Enter at 10:30 AM
```

### `all_conditions(elements)`
Combines multiple rules with AND logic. All conditions must be met simultaneously.

**Parameters:**
- `elements` (list): List of coroutine rule objects

**Example:**
```python
entry_rules=[
    all_conditions([
        initial_breakout(30),
        time_based(10, 0)  # Enter only if breakout occurs AND it's 10:00 AM
    ])
]
```

## Available Exit Rules

### `stop_loss(percent)`
Exits position when price falls below entry price by specified percentage.

**Parameters:**
- `percent` (float): Loss threshold as decimal (e.g., 0.02 for 2%)

**Example:**
```python
exit_rules=[stop_loss(0.02)]  # Exit if position loses 2%
```

### `stop_profit(percent)`
Exits position when price rises above entry price by specified percentage.

**Parameters:**
- `percent` (float): Profit target as decimal (e.g., 0.03 for 3%)

**Example:**
```python
exit_rules=[stop_profit(0.03)]  # Exit if position gains 3%
```

### `time_based(hour, minute)`
Exits position at a specific time (also usable as exit rule).

**Example:**
```python
exit_rules=[time_based(15, 45)]  # Exit at 3:45 PM
```

## Building Custom Rules

The framework uses Python coroutines (generators) to implement trading rules. This pattern allows rules to maintain state across market data updates and generate signals when conditions are met.

### Understanding the Coroutine Pattern

Each rule is a generator function decorated with `@coroutine` that:
1. Receives market data points via `yield`
2. Maintains internal state between calls
3. Yields a `Signal` object when conditions are met
4. Can reset state as needed (e.g., daily resets)

### Input Format

Rules receive a tuple `(point, df)` where:
- `point`: A `Point` namedtuple with `(time_stamp, price)`
- `df`: DataFrame with historical data (currently unused, reserved for future features)

### Signal Format

When conditions are met, yield a `Signal` object:

```python
from signals import Signal

yield Signal(
    point=point,              # Current market data point
    desc='signal description' # Human-readable description
)
```

For entry rules, you can optionally specify equity percentage:

```python
yield Signal(
    point=point,
    desc='entry signal',
    equity_pct=0.75  # Use 75% of available equity (overrides Config.equity_pct)
)
```

### Example 1: Simple Price Threshold Entry Rule

```python
from coroutines import coroutine
from signals import Signal

@coroutine
def price_above(threshold):
    """Generate entry signal when price exceeds threshold."""
    while True:
        point, _ = (yield)
        if point.price > threshold:
            yield Signal(
                point=point,
                desc=f'price above {threshold}'
            )
```

**Usage:**
```python
config = Config(
    symbol='IVV',
    equity_pct=0.50,
    entry_rules=[price_above(250.0)],
    exit_rules=[stop_loss(0.02)]
)
```

### Example 2: Price Range Entry Rule (Stateful)

```python
@coroutine
def price_in_range(min_price, max_price, consecutive_minutes=3):
    """Generate signal after price stays in range for consecutive periods."""
    consecutive_count = 0

    while True:
        point, _ = (yield)

        if min_price <= point.price <= max_price:
            consecutive_count += 1
            if consecutive_count >= consecutive_minutes:
                yield Signal(
                    point=point,
                    desc=f'price in range [{min_price}, {max_price}] for {consecutive_minutes} min'
                )
                consecutive_count = 0  # Reset after signal
        else:
            consecutive_count = 0  # Reset if out of range
```

**Usage:**
```python
entry_rules=[price_in_range(248.0, 252.0, consecutive_minutes=5)]
```

### Example 3: Moving Average Crossover (Advanced)

```python
from collections import deque

@coroutine
def moving_average_crossover(short_period, long_period):
    """Generate signal when short MA crosses above long MA."""
    short_prices = deque(maxlen=short_period)
    long_prices = deque(maxlen=long_period)
    prev_short_ma = None
    prev_long_ma = None

    while True:
        point, _ = (yield)

        short_prices.append(point.price)
        long_prices.append(point.price)

        # Wait until we have enough data
        if len(short_prices) < short_period or len(long_prices) < long_period:
            continue

        short_ma = sum(short_prices) / len(short_prices)
        long_ma = sum(long_prices) / len(long_prices)

        # Detect crossover (short crosses above long)
        if prev_short_ma is not None and prev_long_ma is not None:
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                yield Signal(
                    point=point,
                    desc=f'MA crossover: {short_period} above {long_period}'
                )

        prev_short_ma = short_ma
        prev_long_ma = long_ma
```

**Usage:**
```python
entry_rules=[moving_average_crossover(short_period=5, long_period=20)]
```

### Example 4: Daily Reset Pattern

Many rules need to reset state at the start of each trading day:

```python
import datetime

@coroutine
def daily_high_breakout():
    """Generate signal when price breaks above the day's high."""
    current_date = None
    daily_high = 0
    signal_generated = False

    while True:
        point, _ = (yield)

        # Check if it's a new day
        if point.time_stamp.date() != current_date:
            current_date = point.time_stamp.date()
            daily_high = point.price
            signal_generated = False
        else:
            # Update daily high
            daily_high = max(daily_high, point.price)

            # Generate signal if breakout occurs (once per day)
            if not signal_generated and point.price > daily_high:
                signal_generated = True
                yield Signal(
                    point=point,
                    desc=f'broke above daily high: {daily_high}'
                )
```

### Example 5: Volume-Based Entry (Using DataFrame)

If you extend the framework to include volume data in the DataFrame:

```python
@coroutine
def volume_spike(threshold_multiplier=2.0):
    """Generate signal when volume exceeds average by threshold."""
    while True:
        point, df = (yield)

        if df is None or len(df) < 20:
            continue

        # Calculate average volume from last 20 periods
        avg_volume = df['volume'].tail(20).mean()
        current_volume = df['volume'].iloc[-1]

        if current_volume > avg_volume * threshold_multiplier:
            yield Signal(
                point=point,
                desc=f'volume spike: {current_volume:.0f} vs avg {avg_volume:.0f}'
            )
```

### Example 6: Time-Window Entry Rule

```python
@coroutine
def time_window_entry(start_hour, start_minute, end_hour, end_minute):
    """Generate signal only during specific time window (once)."""
    signal_generated = False
    current_date = None

    while True:
        point, _ = (yield)

        # Reset daily
        if point.time_stamp.date() != current_date:
            current_date = point.time_stamp.date()
            signal_generated = False

        if signal_generated:
            continue

        # Check if within time window
        current_time = point.time_stamp.time()
        start_time = datetime.time(start_hour, start_minute)
        end_time = datetime.time(end_hour, end_minute)

        if start_time <= current_time <= end_time:
            signal_generated = True
            yield Signal(
                point=point,
                desc=f'entered during window {start_hour}:{start_minute}-{end_hour}:{end_minute}'
            )
```

**Usage:**
```python
entry_rules=[time_window_entry(10, 0, 11, 30)]  # Enter between 10:00-11:30 AM
```

### Example 7: Trailing Stop Exit Rule

```python
@coroutine
def trailing_stop(trail_percent):
    """Exit when price falls below trailing stop level."""
    highest_price = 0
    trailing_stop_level = 0

    while True:
        point, _ = (yield)

        # Update highest price and trailing stop
        if point.price > highest_price:
            highest_price = point.price
            trailing_stop_level = highest_price * (1 - trail_percent)

        # Check if stop is hit
        if highest_price > 0 and point.price < trailing_stop_level:
            yield Signal(
                point=point,
                desc=f'trailing stop hit: {trailing_stop_level:.2f}'
            )
            # Reset
            highest_price = 0
            trailing_stop_level = 0
```

**Usage:**
```python
exit_rules=[trailing_stop(0.03)]  # Trail by 3%
```

### Combining Custom Rules

Use `all_conditions()` to combine multiple custom rules with AND logic:

```python
from coroutines import all_conditions

entry_rules=[
    all_conditions([
        price_above(250.0),
        time_window_entry(10, 0, 14, 0),
        moving_average_crossover(5, 20)
    ])
]
```

This generates an entry signal only when ALL conditions are met simultaneously.

### Best Practices

1. **Use the @coroutine decorator**: Always decorate your rule functions
2. **Prime with (yield)**: Start with `point, _ = (yield)` to receive first input
3. **Reset state appropriately**: Reset counters/flags when conditions change or daily
4. **Handle edge cases**: Check for None/empty data before calculations
5. **Descriptive signals**: Provide clear `desc` messages for debugging and chart annotations
6. **Test thoroughly**: Write unit tests for your custom rules (see `tests/test_coroutines.py`)
7. **Avoid look-ahead bias**: Only use data available up to current point in time

### Testing Custom Rules

Follow the pattern in `tests/test_coroutines.py`:

```python
import unittest
from core import Point
import datetime

class TestCustomRules(unittest.TestCase):
    def test_price_above(self):
        rule = price_above(250.0)

        # Test below threshold
        point1 = Point(datetime.datetime(2020, 4, 1, 10, 0), 249.0)
        signal = rule.send((point1, None))
        self.assertIsNone(signal)

        # Test above threshold
        point2 = Point(datetime.datetime(2020, 4, 1, 10, 1), 251.0)
        signal = rule.send((point2, None))
        self.assertIsNotNone(signal)
        self.assertEqual(signal.point.price, 251.0)
```

## Data Format

Historical data should be CSV files in the `data/` directory with the following format:

```csv
timestamp,price
2020-04-01 09:30:00,248.9
2020-04-01 09:31:00,249.1
2020-04-01 09:32:00,248.8
```

**Requirements:**
- No header row
- Two columns: timestamp, price
- Timestamp format: `YYYY-MM-DD HH:MM:SS`
- File naming: `{SYMBOL}.csv` (e.g., `IVV.csv`)

## Configuration

### Logging

Logging configuration is in `settings/logging.conf`. Default setup:
- Logs to stdout
- Log level: DEBUG
- Format: `%(asctime)s - %(levelname)s - %(message)s`

### Trading Parameters

**Function Signature:**
```python
run(configs, live=False, specific_day=None, cash=25000, commission=0, interval=1, save_charts=True)
```

**Parameters:**
- `configs` (list): List of Config objects defining strategies
- `live` (bool): False for backtesting, True for live trading
- `specific_day` (datetime): Run against specific date (None = all data)
- `cash` (float): Starting capital in dollars (default: $25,000)
- `commission` (float): Commission per share in dollars (default: $0)
- `interval` (int): Polling interval in minutes for live mode (default: 1)
- `save_charts` (bool): Generate HTML charts (default: True)

## Output

### Charts

Charts are saved to:
- Backtesting: `./charts/testing/`
- Live trading: `./charts/live/`

**Chart Types:**
- Single strategy/day: `{date}_{symbol}.html`
- Combined multi-strategy: `{date}_combined.html`
- Combined multi-day: `{symbol}_combined.html`

Charts display:
- Price action over time
- Buy markers (green triangles)
- Sell markers (red triangles)
- Signal descriptions on hover

### P&L Reports

Console output includes:
- Per-symbol position quantities
- Realized P&L
- Mark-to-market (unrealized) P&L
- Total commissions
- Available cash
- Combined P&L across all positions

Example:
```
Symbol: IVV
  Position: 0
  Realized PL: $125.50
  MTM PL: $0.00
  Commissions: $2.50
  Total PL: $123.00

Available Cash: $25,123.00
Total PL: $123.00
```

## Architecture

### Core Components

- **app.py**: Main event loop and entry point
- **core.py**: Domain objects (Strategy, Config, Trade, Point)
- **coroutines.py**: Trading signal generators using coroutine pattern
- **positions.py**: Position and P&L tracking (Singleton)
- **signals.py**: Signal data structure
- **data_providers.py**: Abstraction for CSV vs live data sources
- **custom.py**: Broker integration stubs (requires implementation)
- **utils.py**: Plotting and utility functions

### Design Pattern

The framework uses **coroutines (generators)** as the primary design pattern for implementing trading rules. This enables:
- Stateful evaluation of market conditions
- Event-driven processing of market data
- Clean separation of rule logic from execution

## Testing

Run unit tests:
```bash
python -m unittest discover tests
```

**Test Coverage:**
- `tests/test_coroutines.py`: Entry/exit rule logic
- `tests/test_positions.py`: Position tracking and P&L calculations

## Live Trading Setup

To enable live trading, implement the following functions in `custom.py`:

### `get_data_point(symbol)`
Fetch real-time price data from your data provider.

**Returns:** `Point(time_stamp, price)`

### `submit_order(symbol, qty, is_entry)`
Submit order to your broker's API.

**Parameters:**
- `symbol` (str): Trading symbol
- `qty` (int): Quantity to trade
- `is_entry` (bool): True for buy, False for sell

**Returns:** Executed price (float)

## End-to-End Testing

The framework includes a comprehensive end-to-end test that demonstrates the complete workflow from data generation through chart creation.

### Running the E2E Test

```bash
python test_e2e.py
```

This automated test performs the following steps:

1. **Generates Synthetic Test Data**
   - Creates 3 days of realistic intraday price data for symbol 'TEST'
   - Simulates opening gaps, intraday volatility, and breakout patterns
   - Saves to `data/TEST.csv` (1,170 price points)

2. **Runs Backtests**
   - Tests a 45-minute breakout strategy with 2% exits on 2020-04-01
   - Tests a 30-minute breakout strategy with 1% exits on 2020-04-02
   - Demonstrates different strategy configurations and their results

3. **Generates Interactive Charts**
   - Creates HTML charts showing price action, buy/sell signals, and P&L
   - Saves charts to `charts/testing/` directory
   - Each chart is approximately 4.7MB with full Plotly interactivity

4. **Validates Results**
   - Verifies chart files were created successfully
   - Reports P&L for each backtest run
   - Provides file locations and next steps

### Example Output

When you run the E2E test, you'll see output like this:

```
======================================================================
STEP 1: Generating Synthetic Test Data
======================================================================
Generated 1170 price points for TEST
Saved to: ./data/TEST.csv
Date range: 2020-04-01 to 2020-04-03
Price range: $251.06 to $289.52

======================================================================
STEP 2: Running Single Strategy Backtest (Specific Day)
======================================================================
Strategy: 45-minute breakout with 2% stop loss/profit
Testing date: 2020-04-01

Executing signal: break out (entry at $259.93)
Executing signal: profit exit: broke above $264.945
PnlReport(starting_equity=25000, ending_equity=25269, net=269, total_pl=269)

======================================================================
STEP 3: Running Alternative Strategy Configuration
======================================================================
Strategy: 30-minute breakout with tighter 1% exits
Testing date: 2020-04-02

Executing signal: break out (entry at $287.54)
Executing signal: profit exit: broke above $294.415
PnlReport(starting_equity=25000, ending_equity=25462, net=462, total_pl=462)

======================================================================
STEP 4: Verifying Chart Generation
======================================================================
SUCCESS: Generated 2 chart files:
  - 2020-04-01_TEST.html (4,789,092 bytes)
  - 2020-04-02_TEST.html (4,789,087 bytes)

Charts location: /Users/your-path/intraday/charts/testing
```

### Understanding the Charts

The generated HTML charts are interactive Plotly visualizations that display:

**Visual Elements:**
- **Blue Line**: Intraday price movement (1-minute bars)
- **Green Triangles (▲)**: Buy signals with entry descriptions
- **Red Triangles (▼)**: Sell signals with exit descriptions
- **Title**: Shows symbol, date, P&L, and final position size

**Interactive Features:**
- Hover over any point to see exact time and price
- Hover over buy/sell markers to see signal descriptions
- Zoom in/out by dragging or using the toolbar
- Pan across the chart to examine different time periods
- Download as PNG using the camera icon

**Example Chart Interpretation:**

For the 2020-04-01 test with 45-minute breakout strategy:
1. Price opens at $251.06 at 9:30 AM
2. System observes first 45 minutes (9:30-10:15) and tracks high of $259.93
3. At 10:15 AM, price breaks above $259.93, triggering entry signal (green triangle)
4. Position entered: ~48 shares at $259.93 (50% of $25,000 cash)
5. At 10:20 AM, price reaches $266.66, exceeding 2% profit target
6. Exit signal triggered (red triangle), position closed
7. **Result**: $269 profit (+1.08% return on capital)

### Customizing the E2E Test

Edit `test_e2e.py` to experiment with different strategies:

```python
# Modify strategy parameters
config = Config(
    symbol='TEST',
    equity_pct=0.75,  # Use 75% of capital instead of 50%
    entry_rules=[initial_breakout(30)],  # Shorter observation period
    exit_rules=[
        stop_loss(0.015),      # Tighter stop loss (1.5%)
        stop_profit(0.025),    # Wider profit target (2.5%)
        time_based(15, 0)      # Earlier exit time (3:00 PM)
    ]
)
```

Then re-run: `python test_e2e.py`

### Generating Custom Test Data

Use `generate_test_data.py` to create different market scenarios:

```python
from generate_test_data import generate_multi_day_data, save_to_csv
import random

random.seed(123)  # Different random seed = different price patterns

prices = generate_multi_day_data(
    symbol='CUSTOM',
    num_days=5,         # More trading days
    start_price=100.0   # Different starting price
)

save_to_csv('CUSTOM', prices)
```

Then update your strategy config to use `symbol='CUSTOM'`.

### What to Look For in Charts

**Successful Trades:**
- Entry and exit markers clearly visible
- Positive P&L in title
- Exit triggered by profit target (desired outcome)

**Strategy Issues to Identify:**
- Too many false signals (multiple entries without exits)
- Stop loss triggers (indicates strategy needs refinement)
- No signals generated (parameters may be too strict)
- Late entries/exits missing optimal prices

### Using E2E Tests for Development

The E2E test serves multiple purposes:

1. **Validation**: Ensures all components work together correctly
2. **Demonstration**: Shows new users how the system operates
3. **Regression Testing**: Verify changes don't break existing functionality
4. **Strategy Development**: Quick iteration on strategy parameters
5. **Documentation**: Provides concrete examples with real output

Run `python test_e2e.py` after any code changes to ensure the system still works end-to-end.

## Limitations

- **Live trading requires implementation**: `custom.py` contains stubs only
- **No order types**: Market orders only (no limit, stop orders)
- **US market hours only**: 9:30 AM - 4:00 PM ET
- **Long-only**: No short selling support
- **Single-day positions**: All positions closed at 15:59

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions, please open an issue on GitHub: https://github.com/repque/intraday/issues
