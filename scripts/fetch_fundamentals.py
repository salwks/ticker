#!/usr/bin/env python3
"""
Quarterly Fundamentals Crawler (yfinance version with symbol normalization)
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

def normalize_for_yfinance(symbol):
    """Convert NASDAQ format (BRK.B) to yfinance format (BRK-B)"""
    return symbol.replace('.', '-')

def normalize_for_storage(symbol):
    """Convert yfinance format back to NASDAQ format for consistency"""
    return symbol.replace('-', '.')

def get_fundamentals(symbol):
    """Fetch fundamental data for a single symbol using yfinance"""
    # Convert symbol for yfinance API
    yf_symbol = normalize_for_yfinance(symbol)
    
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        # Check if ticker exists
        if not info or 'symbol' not in info:
            print(f"  ⚠️  {symbol}: Not found")
            return None
        
        # Extract fundamentals (기존 필드)
        fundamentals = {
            'roe': info.get('returnOnEquity'),
            'debtToEquity': info.get('debtToEquity'),
            'currentRatio': info.get('currentRatio'),
            'eps': info.get('trailingEps'),
            'dividendRate': info.get('dividendRate'),
            'dividendYield': info.get('dividendYield'),
            'profitMargin': info.get('profitMargins'),
            'bookValue': info.get('bookValue'),
            # 버핏 스코어용 추가 필드
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
            'returnOnAssets': info.get('returnOnAssets')
        }

        # Convert percentages (yfinance returns decimals)
        if fundamentals['roe'] is not None:
            fundamentals['roe'] *= 100
        if fundamentals['dividendYield'] is not None:
            fundamentals['dividendYield'] *= 100
        if fundamentals['profitMargin'] is not None:
            fundamentals['profitMargin'] *= 100
        if fundamentals['operatingMargins'] is not None:
            fundamentals['operatingMargins'] *= 100
        if fundamentals['grossMargins'] is not None:
            fundamentals['grossMargins'] *= 100
        if fundamentals['revenueGrowth'] is not None:
            fundamentals['revenueGrowth'] *= 100
        if fundamentals['earningsGrowth'] is not None:
            fundamentals['earningsGrowth'] *= 100
        if fundamentals['returnOnAssets'] is not None:
            fundamentals['returnOnAssets'] *= 100
        
        return fundamentals
        
    except Exception as e:
        print(f"  ❌ {symbol}: {str(e)}")
        return None

def load_ticker_list():
    """Load ticker symbols from sp500.json (S&P 500 only)"""
    sp500_file = 'data/sp500.json'

    if not os.path.exists(sp500_file):
        print(f"❌ S&P 500 file not found: {sp500_file}")
        sys.exit(1)

    with open(sp500_file, 'r') as f:
        data = json.load(f)
        return data['symbols']

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
            # Store with NASDAQ format (original symbol)
            results[symbol] = data
            print("✅")
        else:
            errors += 1
        
        # Random delay to be respectful
        if i < len(symbols):
            delay = uniform(0.3, 1.0)
            sleep(delay)
    
    print(f"\n✅ Completed: {len(results)} success, {errors} errors")
    print(f"📝 Note: Symbols stored in NASDAQ format (e.g., BRK.B)")
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
        # Test with 10 symbols (using NASDAQ format from tickers.json)
        test_symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 
                       'META', 'TSLA', 'BRK.B', 'V', 'JPM']
        print("🧪 TEST MODE: Crawling 10 symbols only")
        print("📝 Note: Using NASDAQ format (BRK.B), will convert to BRK-B for yfinance")
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
