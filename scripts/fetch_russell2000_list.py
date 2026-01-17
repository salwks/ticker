#!/usr/bin/env python3
"""
Russell 2000 Index Constituents Fetcher
Fetches Russell 2000 symbols from Wikipedia or similar source
Updates quarterly (same schedule as fundamentals, but +7 days)
"""

import requests
import json
import os
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from metadata_utils import update_indices_count

OUTPUT_FILE = 'data/russell2000.json'
SP500_FILE = 'data/sp500.json'

def fetch_russell2000_from_ishares():
    """
    Fetch Russell 2000 constituents from iShares IWM ETF holdings
    This is more reliable than Wikipedia scraping
    """
    print("📡 Fetching Russell 2000 from iShares IWM holdings...")

    # iShares IWM (Russell 2000 ETF) holdings CSV
    url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse CSV (skip header rows)
        lines = response.text.split('\n')
        symbols = []

        # Find the header row and data start
        data_started = False
        for line in lines:
            if 'Ticker' in line and 'Name' in line:
                data_started = True
                continue

            if data_started and line.strip():
                parts = line.split(',')
                if len(parts) >= 2:
                    ticker = parts[0].strip().strip('"')
                    # Skip non-stock entries
                    if ticker and not ticker.startswith('-') and len(ticker) <= 5:
                        symbols.append(ticker)

        print(f"✅ Found {len(symbols)} symbols from iShares")
        return symbols

    except Exception as e:
        print(f"❌ iShares fetch failed: {e}")
        return None

def fetch_russell2000_fallback():
    """
    Fallback: Use a curated list of Russell 2000-like small cap stocks
    This is a simplified approach for testing
    """
    print("⚠️ Using fallback Russell 2000 list...")

    # In production, you would have a more complete list
    # For now, returning empty to indicate we need real data
    return []

def load_sp500_symbols():
    """Load S&P 500 symbols to exclude from Russell 2000"""
    if os.path.exists(SP500_FILE):
        with open(SP500_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('symbols', []))
    return set()

def filter_duplicates(russell_symbols, sp500_symbols):
    """Remove any symbols that are in S&P 500"""
    filtered = [s for s in russell_symbols if s not in sp500_symbols]
    removed = len(russell_symbols) - len(filtered)
    if removed > 0:
        print(f"🔄 Removed {removed} duplicates (also in S&P 500)")
    return filtered

def save_results(symbols):
    """Save Russell 2000 symbols to JSON"""
    os.makedirs('data', exist_ok=True)

    output = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'count': len(symbols),
        'symbols': sorted(symbols)
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    # Update metadata
    update_indices_count(russell2000_count=len(symbols))

    print(f"💾 Saved to {OUTPUT_FILE}")
    print(f"📊 Total: {len(symbols)} symbols")

def main():
    print("🚀 Fetching Russell 2000 Index Constituents")
    print("=" * 50)

    # Load S&P 500 for duplicate check
    sp500_symbols = load_sp500_symbols()
    print(f"📋 Loaded {len(sp500_symbols)} S&P 500 symbols for duplicate check")

    # Try primary source
    symbols = fetch_russell2000_from_ishares()

    # Fallback if primary fails
    if not symbols or len(symbols) < 1000:
        print("⚠️ Primary source returned insufficient data")
        fallback = fetch_russell2000_fallback()
        if fallback:
            symbols = fallback

    if not symbols:
        print("❌ Failed to fetch Russell 2000 symbols")
        sys.exit(1)

    # Remove duplicates with S&P 500
    symbols = filter_duplicates(symbols, sp500_symbols)

    # Save results
    save_results(symbols)

    print("\n✅ Russell 2000 list update complete!")

if __name__ == '__main__':
    main()
