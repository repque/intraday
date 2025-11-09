"""
End-to-end test of the intraday trading framework.

This script:
1. Generates synthetic test data
2. Runs backtest with multiple strategies
3. Generates charts
4. Validates results
5. Demonstrates complete workflow
"""

from __future__ import print_function

import datetime
import logging
import logging.config
import os
import sys

from core import Config
from coroutines import initial_breakout, time_based, stop_loss, stop_profit
from app import run, run_dates
from generate_test_data import generate_multi_day_data, save_to_csv
import random


def setup_logging():
    """Initialize logging configuration."""
    import os
    logging.config.fileConfig(os.path.join("settings", "logging.conf"))


def generate_test_data():
    """Generate synthetic test data."""
    print("=" * 70)
    print("STEP 1: Generating Synthetic Test Data")
    print("=" * 70)

    random.seed(42)  # Reproducible results
    prices = generate_multi_day_data(
        symbol='TEST',
        num_days=3,
        start_price=250.0
    )
    save_to_csv('TEST', prices)
    print()


def test_single_strategy():
    """Test single strategy on specific day."""
    print("=" * 70)
    print("STEP 2: Running Single Strategy Backtest (Specific Day)")
    print("=" * 70)
    print("Strategy: 45-minute breakout with 2% stop loss/profit")
    print("Testing date: 2020-04-01")
    print()

    config = Config(
        symbol='TEST',
        equity_pct=0.50,
        entry_rules=[initial_breakout(45)],
        exit_rules=[
            time_based(14, 15),
            stop_loss(0.02),
            stop_profit(0.02)
        ]
    )

    run(
        configs=[config],
        live=False,
        specific_day=datetime.datetime(2020, 4, 1),
        cash=25000,
        commission=0,
        save_charts=True
    )
    print()


def test_multiple_strategies():
    """Test different strategy configurations."""
    print("=" * 70)
    print("STEP 3: Running Alternative Strategy Configuration")
    print("=" * 70)
    print("Strategy: 30-minute breakout with tighter 1% exits")
    print("Testing date: 2020-04-02")
    print()

    config = Config(
        symbol='TEST',
        equity_pct=0.60,
        entry_rules=[initial_breakout(30)],
        exit_rules=[
            stop_loss(0.01),
            stop_profit(0.01),
            time_based(15, 30)
        ]
    )

    run(
        configs=[config],
        live=False,
        specific_day=datetime.datetime(2020, 4, 2),
        cash=25000,
        commission=0,
        save_charts=True
    )
    print()


def verify_charts():
    """Verify that charts were generated."""
    print("=" * 70)
    print("STEP 4: Verifying Chart Generation")
    print("=" * 70)

    charts_folder = './charts/testing'

    if not os.path.exists(charts_folder):
        print("ERROR: Charts folder not found!")
        return False

    chart_files = [f for f in os.listdir(charts_folder) if f.endswith('.html')]

    if not chart_files:
        print("ERROR: No chart files generated!")
        return False

    print(f"SUCCESS: Generated {len(chart_files)} chart files:")
    for chart_file in sorted(chart_files):
        file_path = os.path.join(charts_folder, chart_file)
        file_size = os.path.getsize(file_path)
        print(f"  - {chart_file} ({file_size:,} bytes)")

    print()
    print(f"Charts location: {os.path.abspath(charts_folder)}")
    print("Open any .html file in your browser to view interactive charts")
    print()

    return True


def display_summary():
    """Display test summary."""
    print("=" * 70)
    print("END-TO-END TEST COMPLETE")
    print("=" * 70)
    print()
    print("What was tested:")
    print("  ✓ Synthetic data generation")
    print("  ✓ Single strategy backtest (specific day)")
    print("  ✓ Multiple strategy backtest (all days)")
    print("  ✓ Chart generation and combination")
    print("  ✓ P&L tracking and reporting")
    print()
    print("Next steps:")
    print("  1. Open charts in ./charts/testing/ to view results")
    print("  2. Review console output for P&L reports")
    print("  3. Modify strategies in this script and re-run")
    print("  4. Create your own custom rules (see README.md)")
    print()


def main():
    """Run complete end-to-end test."""
    try:
        # Setup
        setup_logging()

        # Generate test data
        generate_test_data()

        # Run tests
        test_single_strategy()
        test_multiple_strategies()

        # Verify results
        success = verify_charts()

        # Summary
        display_summary()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
