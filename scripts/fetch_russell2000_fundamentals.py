#!/usr/bin/env python3
"""
Russell 2000 Fundamentals Crawler (Batch Mode)
Crawls 1/3 of Russell 2000 per run to avoid rate limiting
Runs quarterly: +7 days after S&P 500 (12th, 15th, 18th of Feb, May, Aug, Nov)

Environment Variables:
  BATCH: 1, 2, or 3 (which third to crawl)

Schedule:
  Batch 1: 12th of month (symbols 0-666)
  Batch 2: 15th of month (symbols 667-1333)
  Batch 3: 18th of month (symbols 1334-2000)
"""

import yfinance as yf
import json
import os
from datetime import datetime
from time import sleep
from random import uniform
import sys

# Configuration
FUNDAMENTALS_FILE = 'data/fundamentals.json'
RUSSELL_FILE = 'data/russell2000.json'
BATCH_SIZE = 667  # ~2000 / 3

def normalize_for_yfinance(symbol):
    """Convert NASDAQ format (BRK.B) to yfinance format (BRK-B)"""
    return symbol.replace('.', '-')

def get_fundamentals(symbol):
    """Fetch fundamental data for a single symbol using yfinance"""
    yf_symbol = normalize_for_yfinance(symbol)

    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        if not info or 'symbol' not in info:
            print(f"  ⚠️  {symbol}: Not found")
            return None

        fundamentals = {
            'roe': info.get('returnOnEquity'),
            'debtToEquity': info.get('debtToEquity'),
            'currentRatio': info.get('currentRatio'),
            'eps': info.get('trailingEps'),
            'dividendRate': info.get('dividendRate'),
            'dividendYield': info.get('dividendYield'),
            'profitMargin': info.get('profitMargins'),
            'bookValue': info.get('bookValue'),
            'totalDebt': info.get('totalDebt'),
            'netIncomeToCommon': info.get('netIncomeToCommon'),
            'freeCashflow': info.get('freeCashflow'),
            'operatingMargins': info.get('operatingMargins'),
            'grossMargins': info.get('grossMargins'),
            'totalCash': info.get('totalCash'),
            'totalRevenue': info.get('totalRevenue'),
            'operatingCashflow': info.get('operatingCashflow'),
            'revenueGrowth': info.get('revenueGrowth'),
            'earningsGrowth': info.get('earningsGrowth'),
            'quickRatio': info.get('quickRatio'),
            'returnOnAssets': info.get('returnOnAssets'),
            'sector': info.get('sector'),  # GICS sector (e.g., "Technology", "Financial Services")
            'index': 'russell2000'  # Mark as Russell 2000
        }

        # Convert percentages
        for key in ['roe', 'dividendYield', 'profitMargin', 'operatingMargins',
                    'grossMargins', 'revenueGrowth', 'earningsGrowth', 'returnOnAssets']:
            if fundamentals.get(key) is not None:
                fundamentals[key] *= 100

        return fundamentals

    except Exception as e:
        print(f"  ❌ {symbol}: {str(e)}")
        return None

def load_russell_symbols():
    """Load Russell 2000 symbols"""
    if not os.path.exists(RUSSELL_FILE):
        print(f"❌ Russell 2000 file not found: {RUSSELL_FILE}")
        sys.exit(1)

    with open(RUSSELL_FILE, 'r') as f:
        data = json.load(f)
        return data['symbols']

def load_existing_fundamentals():
    """Load existing fundamentals.json to merge with"""
    if os.path.exists(FUNDAMENTALS_FILE):
        with open(FUNDAMENTALS_FILE, 'r') as f:
            return json.load(f)
    return {'data': {}}

def get_batch_symbols(all_symbols, batch_num):
    """Get symbols for specific batch (1, 2, or 3)"""
    start = (batch_num - 1) * BATCH_SIZE
    end = start + BATCH_SIZE if batch_num < 3 else len(all_symbols)
    return all_symbols[start:end]

def crawl_batch(symbols):
    """Crawl fundamentals for batch of symbols"""
    print(f"📊 Crawling fundamentals for {len(symbols)} symbols...")
    print(f"⏱️  Estimated time: {len(symbols) * 1.5 / 60:.1f} minutes")

    results = {}
    errors = 0

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}...", end=' ')

        data = get_fundamentals(symbol)
        if data:
            results[symbol] = data
            print("✅")
        else:
            errors += 1

        if i < len(symbols):
            delay = uniform(0.3, 1.0)
            sleep(delay)

    print(f"\n✅ Completed: {len(results)} success, {errors} errors")
    return results

def save_results(new_data, batch_num):
    """Merge new data into existing fundamentals.json"""
    existing = load_existing_fundamentals()

    # Merge new data
    if 'data' not in existing:
        existing['data'] = {}

    for symbol, data in new_data.items():
        existing['data'][symbol] = data

    # Update metadata
    month = datetime.now().month
    quarter_map = {2: 'Q4', 5: 'Q1', 8: 'Q2', 11: 'Q3'}
    quarter = quarter_map.get(month, f'Q{(month-1)//3 + 1}')

    existing['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    existing['quarter'] = f"{datetime.now().year}-{quarter}"
    existing['count'] = len(existing['data'])

    with open(FUNDAMENTALS_FILE, 'w') as f:
        json.dump(existing, f, indent=2)

    print(f"💾 Merged {len(new_data)} symbols into {FUNDAMENTALS_FILE}")
    print(f"📊 Total symbols now: {existing['count']}")

def main():
    # Get batch number from environment or args
    batch_num = int(os.environ.get('BATCH', 1))
    if len(sys.argv) > 1:
        batch_num = int(sys.argv[1])

    if batch_num not in [1, 2, 3]:
        print("❌ BATCH must be 1, 2, or 3")
        sys.exit(1)

    print(f"🚀 Russell 2000 Fundamentals Crawler - Batch {batch_num}/3")
    print("=" * 50)

    # Load Russell 2000 symbols
    all_symbols = load_russell_symbols()
    print(f"📋 Total Russell 2000 symbols: {len(all_symbols)}")

    # Get batch
    batch_symbols = get_batch_symbols(all_symbols, batch_num)
    print(f"📦 Batch {batch_num}: {len(batch_symbols)} symbols")

    if not batch_symbols:
        print("⚠️ No symbols to process")
        sys.exit(0)

    # Crawl
    results = crawl_batch(batch_symbols)

    # Save (merge into existing)
    if results:
        save_results(results, batch_num)
        print(f"\n✅ Batch {batch_num} complete!")
    else:
        print("\n❌ No data collected")
        sys.exit(1)

if __name__ == '__main__':
    main()
