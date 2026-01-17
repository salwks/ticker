#!/usr/bin/env python3
"""
Daily Technical Data Crawler
Crawls price history and calculates RSI, SMA 200, MDD
Runs daily after market close (EST 5pm = UTC 10pm)
"""

import yfinance as yf
import json
import os
from datetime import datetime
from time import sleep
from random import uniform
import sys
from metadata_utils import update_technical_metadata

# Configuration
OUTPUT_FILE = 'data/technical_data.json'
HISTORY_PERIOD = '1y'  # 1 year for initial crawl

def normalize_for_yfinance(symbol):
    """Convert NASDAQ format (BRK.B) to yfinance format (BRK-B)"""
    return symbol.replace('.', '-')

def calculate_sma(prices, period=200):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_mdd(current_price, high_52w):
    """Calculate Maximum Drawdown from 52-week high"""
    if high_52w == 0:
        return 0
    return round(((current_price - high_52w) / high_52w) * 100, 2)

def get_technical_data(symbol):
    """Fetch technical data for a single symbol"""
    yf_symbol = normalize_for_yfinance(symbol)
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # Fetch 1 year history
        history = ticker.history(period=HISTORY_PERIOD)
        
        if history.empty or len(history) < 50:
            print(f"  ⚠️  {symbol}: Insufficient data")
            return None
        
        # Extract price data
        closes = history['Close'].tolist()
        highs = history['High'].tolist()
        
        # Current values
        current_price = round(closes[-1], 2)
        high_52w = round(max(highs), 2)
        
        # Calculate indicators
        sma200 = calculate_sma(closes, 200)
        rsi = calculate_rsi(closes, 14)
        mdd = calculate_mdd(current_price, high_52w)
        
        # Simplified history (last 200 days for potential future use)
        recent_history = []
        for i in range(max(0, len(history) - 200), len(history)):
            row = history.iloc[i]
            recent_history.append({
                'date': row.name.strftime('%Y-%m-%d'),
                'close': round(row['Close'], 2),
                'high': round(row['High'], 2)
            })
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'close': current_price,
            'high52w': high_52w,
            'sma200': round(sma200, 2) if sma200 else None,
            'rsi': rsi,
            'mdd': mdd,
            'history': recent_history  # Last 200 days
        }
        
    except Exception as e:
        print(f"  ❌ {symbol}: {str(e)}")
        return None

def load_ticker_list():
    """Load ticker symbols from S&P 500 and Russell 2000"""
    sp500_file = 'data/sp500.json'
    russell_file = 'data/russell2000.json'

    symbols = []

    # Load S&P 500 (required)
    if not os.path.exists(sp500_file):
        print(f"❌ S&P 500 file not found: {sp500_file}")
        sys.exit(1)

    with open(sp500_file, 'r') as f:
        data = json.load(f)
        sp500_symbols = data['symbols']
        symbols.extend(sp500_symbols)
        print(f"📊 Loaded {len(sp500_symbols)} S&P 500 symbols")

    # Load Russell 2000 (optional)
    if os.path.exists(russell_file):
        with open(russell_file, 'r') as f:
            data = json.load(f)
            russell_symbols = data.get('symbols', [])
            # Filter out any duplicates
            new_symbols = [s for s in russell_symbols if s not in symbols]
            symbols.extend(new_symbols)
            print(f"📊 Loaded {len(new_symbols)} Russell 2000 symbols (after dedup)")
    else:
        print(f"⚠️ Russell 2000 file not found, skipping")

    return symbols

def crawl_all(symbols, limit=None):
    """Crawl technical data for all symbols"""
    if limit:
        symbols = symbols[:limit]
    
    print(f"📊 Crawling technical data for {len(symbols)} symbols...")
    print(f"⏱️  Estimated time: {len(symbols) * 1.5 / 60:.1f} minutes")
    
    results = {}
    errors = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}...", end=' ')
        
        data = get_technical_data(symbol)
        if data:
            results[symbol] = data
            print("✅")
        else:
            errors += 1
        
        # Random delay
        if i < len(symbols):
            delay = uniform(0.3, 1.0)
            sleep(delay)
    
    print(f"\n✅ Completed: {len(results)} success, {errors} errors")
    return results

def save_results(data):
    """Save results to JSON file"""
    os.makedirs('data', exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    output = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'date': date_str,
        'count': len(data),
        'data': data
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    # Update metadata.json
    update_technical_metadata(count=len(data), date=date_str)

    print(f"💾 Saved to {OUTPUT_FILE}")
    print(f"📅 Date: {output['date']}")
    print(f"📈 Symbols: {len(data)}")

if __name__ == '__main__':
    # Load S&P 500 symbols
    symbols = load_ticker_list()

    # Crawl
    results = crawl_all(symbols)

    # Save
    if results:
        save_results(results)
        print("\n✅ Technical data update complete!")
    else:
        print("\n❌ No data collected")
        sys.exit(1)
