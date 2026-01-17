#!/usr/bin/env python3
"""
Metadata Utility Functions
Updates metadata.json after each crawl operation
"""

import json
import os
from datetime import datetime

METADATA_FILE = 'data/metadata.json'

def load_metadata():
    """Load current metadata or create default"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)

    # Default structure
    return {
        "fundamentals": {
            "lastUpdated": None,
            "quarter": None,
            "count": 0
        },
        "technical": {
            "lastUpdated": None,
            "date": None,
            "count": 0
        },
        "tickers": {
            "lastUpdated": None,
            "count": 0
        },
        "indices": {
            "sp500": 0,
            "russell2000": 0
        }
    }

def save_metadata(metadata):
    """Save metadata to file"""
    os.makedirs('data', exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"📋 Updated {METADATA_FILE}")

def update_technical_metadata(count, date=None):
    """Update technical data metadata"""
    metadata = load_metadata()
    metadata['technical'] = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'date': date or datetime.now().strftime('%Y-%m-%d'),
        'count': count
    }
    save_metadata(metadata)

def update_fundamentals_metadata(count, quarter=None):
    """Update fundamentals metadata"""
    metadata = load_metadata()

    if not quarter:
        month = datetime.now().month
        quarter_map = {2: 'Q4', 5: 'Q1', 8: 'Q2', 11: 'Q3'}
        q = quarter_map.get(month, f'Q{(month-1)//3 + 1}')
        quarter = f"{datetime.now().year}-{q}"

    metadata['fundamentals'] = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'quarter': quarter,
        'count': count
    }
    save_metadata(metadata)

def update_tickers_metadata(count):
    """Update tickers metadata"""
    metadata = load_metadata()
    metadata['tickers'] = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'count': count
    }
    save_metadata(metadata)

def update_indices_count(sp500_count=None, russell2000_count=None):
    """Update index counts"""
    metadata = load_metadata()
    if sp500_count is not None:
        metadata['indices']['sp500'] = sp500_count
    if russell2000_count is not None:
        metadata['indices']['russell2000'] = russell2000_count
    save_metadata(metadata)
