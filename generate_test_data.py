"""
Generate synthetic intraday price data for testing.

Creates realistic price movements with:
- Opening gap
- Intraday volatility
- Trend patterns
- Breakout scenarios
"""

import csv
import datetime
import random
import math


def generate_intraday_prices(date, open_price, volatility=0.01, trend=0.0005):
    """
    Generate realistic 1-minute intraday prices for a trading day.

    Args:
        date: Trading date
        open_price: Opening price
        volatility: Price volatility (default 1%)
        trend: Intraday trend (default 0.05% per bar)

    Returns:
        List of (timestamp, price) tuples
    """
    prices = []
    current_price = open_price

    # Trading hours: 9:30 AM - 4:00 PM (390 minutes)
    start_time = datetime.datetime.combine(date, datetime.time(9, 30))

    for minute in range(390):
        timestamp = start_time + datetime.timedelta(minutes=minute)

        # Add some realistic price movement
        # Random walk with slight upward trend
        change = random.gauss(trend, volatility)

        # Add some momentum patterns
        if 30 <= minute <= 60:
            # Morning breakout scenario
            change += volatility * 0.5
        elif 180 <= minute <= 210:
            # Afternoon pullback
            change -= volatility * 0.3

        current_price = current_price * (1 + change)
        prices.append((timestamp, round(current_price, 2)))

    return prices


def generate_multi_day_data(symbol, num_days=5, start_price=250.0):
    """
    Generate multiple days of intraday price data.

    Args:
        symbol: Trading symbol
        num_days: Number of trading days to generate
        start_price: Starting price for first day

    Returns:
        List of all (timestamp, price) tuples across all days
    """
    all_prices = []
    current_price = start_price

    # Start from a Monday
    start_date = datetime.date(2020, 4, 1)

    for day_num in range(num_days):
        # Skip weekends
        current_date = start_date + datetime.timedelta(days=day_num)
        if current_date.weekday() >= 5:  # Saturday or Sunday
            continue

        # Add overnight gap (random between -1% and +1%)
        gap = random.uniform(-0.01, 0.01)
        open_price = current_price * (1 + gap)

        # Generate intraday prices with varying volatility
        volatility = random.uniform(0.005, 0.015)
        trend = random.uniform(-0.0003, 0.0008)

        day_prices = generate_intraday_prices(current_date, open_price, volatility, trend)
        all_prices.extend(day_prices)

        # Update current price to closing price
        current_price = day_prices[-1][1]

    return all_prices


def save_to_csv(symbol, prices, data_dir='./data'):
    """
    Save generated prices to CSV file.

    Args:
        symbol: Trading symbol
        prices: List of (timestamp, price) tuples
        data_dir: Directory to save CSV file
    """
    import os

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    filename = f'{data_dir}/{symbol}.csv'

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for timestamp, price in prices:
            writer.writerow([timestamp.strftime('%Y-%m-%d %H:%M:%S'), price])

    print(f'Generated {len(prices)} price points for {symbol}')
    print(f'Saved to: {filename}')
    print(f'Date range: {prices[0][0].date()} to {prices[-1][0].date()}')
    print(f'Price range: ${prices[0][1]:.2f} to ${prices[-1][1]:.2f}')


if __name__ == '__main__':
    # Generate test data for TEST symbol
    random.seed(42)  # For reproducible results

    print('Generating synthetic test data...\n')

    prices = generate_multi_day_data(
        symbol='TEST',
        num_days=3,
        start_price=250.0
    )

    save_to_csv('TEST', prices)
