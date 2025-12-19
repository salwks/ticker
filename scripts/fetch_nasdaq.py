#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)

url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
print(f"📡 Fetching from NASDAQ...")

response = requests.get(url)
response.raise_for_status()

lines = response.text.strip().split('\n')
tickers = []

for line in lines[1:-1]:
    fields = line.split('|')
    if len(fields) < 7:
        continue
    
    # FIXED: Correct field mapping
    symbol = fields[1].strip()  # Symbol
    name = fields[2].strip()    # Security Name
    exchange_code = fields[3].strip()
    etf = fields[6].strip() if len(fields) > 6 else 'N'
    
    if symbol.endswith('.TEST') or symbol.startswith('$') or not symbol:
        continue
    
    if not name or name == 'N/A':
        continue
    
    exchange_map = {'Q': 'NASDAQ', 'N': 'NYSE', 'A': 'AMEX', 'P': 'NYSE ARCA', 'Z': 'BATS'}
    
    tickers.append({
        'symbol': symbol,
        'name': name,
        'exchange': exchange_map.get(exchange_code, 'OTHER'),
        'isETF': etf == 'Y'
    })

output = {
    'lastUpdated': datetime.utcnow().isoformat() + 'Z',
    'count': len(tickers),
    'tickers': sorted(tickers, key=lambda x: x['symbol'])
}

with open('data/tickers.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

with open('data/last_updated.txt', 'w') as f:
    f.write(output['lastUpdated'])

print(f"✅ {len(tickers)} tickers processed")
