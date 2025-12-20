#!/usr/bin/env python3
"""
Quarterly Fundamentals Crawler (yfinance version)
Crawls ROE, Debt/Equity, EPS, and other financial metrics using yfinance
Runs quarterly: Feb 5, May 5, Aug 5, Nov 5
"""

import yfinance as yf
import json
import os
from datetime import datetime
from time import sleep
from random import uniform
import sys

# Configuration
OUTPUT_FILE = 'data/fundamentals.json'

def get_fundamentals(symbol):
    """Fetch fundamental data for a single symbol using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Check if ticker exists
        if not info or 'symbol' not in info:
            print(f"  ⚠️  {symbol}: Not found")
            return None
        
        # Extract fundamentals
        fundamentals = {
            'roe': info.get('returnOnEquity'),
            'debtToEquity': info.get('debtToEquity'),
            'currentRatio': info.get('currentRatio'),
            'eps': info.get('trailingEps'),
            'dividendRate': info.get('dividendRate'),
            'dividendYield': info.get('dividendYield'),
            'profitMargin': info.get('profitMargins'),
            'bookValue': info.get('bookValue')
        }
        
        # Convert percentages (yfinance returns decimals)
        if fundamentals['roe'] is not None:
            fundamentals['roe'] *= 100
        if fundamentals['dividendYield'] is not None:
            fundamentals['dividendYield'] *= 100
        if fundamentals['profitMargin'] is not None:
            fundamentals['profitMargin'] *= 100
        
        return fundamentals
        
    except Exception as e:
        print(f"  ❌ {symbol}: {str(e)}")
        return None

def load_ticker_list():
    """Load ticker symbols from tickers.json"""
    ticker_file = 'data/tickers.json'
    
    if not os.path.exists(ticker_file):
        print(f"❌ Ticker file not found: {ticker_file}")
        sys.exit(1)
    
    with open(ticker_file, 'r') as f:
        data = json.load(f)
        return [t['symbol'] for t in data['tickers']]

def crawl_all(symbols, limit=None):
    """Crawl fundamentals for all symbols"""
    if limit:
        symbols = symbols[:limit]
    
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
        
        # Random delay to be respectful
        if i < len(symbols):
            delay = uniform(0.3, 1.0)
            sleep(delay)
    
    print(f"\n✅ Completed: {len(results)} success, {errors} errors")
    return results

def save_results(data):
    """Save results to JSON file"""
    os.makedirs('data', exist_ok=True)
    
    # Determine quarter
    month = datetime.now().month
    quarter_map = {2: 'Q4', 5: 'Q1', 8: 'Q2', 11: 'Q3'}
    quarter = quarter_map.get(month, f'Q{(month-1)//3 + 1}')
    
    output = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'quarter': f"{datetime.now().year}-{quarter}",
        'count': len(data),
        'data': data
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved to {OUTPUT_FILE}")
    print(f"📊 Quarter: {output['quarter']}")
    print(f"📈 Symbols: {len(data)}")

if __name__ == '__main__':
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    if test_mode:
        # Test with 10 symbols
        test_symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 
                       'META', 'TSLA', 'BRK-B', 'V', 'JPM']
        print("🧪 TEST MODE: Crawling 10 symbols only")
        symbols = test_symbols
    else:
        symbols = load_ticker_list()
    
    # Crawl
    results = crawl_all(symbols, limit=10 if test_mode else None)
    
    # Save
    if results:
        save_results(results)
        print("\n✅ Fundamentals update complete!")
    else:
        print("\n❌ No data collected")
        sys.exit(1)
