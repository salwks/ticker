# Stock Ticker Data
Daily automated updates of US stock tickers.
## �� Data
- **Source**: NASDAQ Trader
- **Updates**: Daily at 2 AM UTC
- **Coverage**: NASDAQ, NYSE, AMEX
## 🚀 Usage
https://raw.githubusercontent.com/salwks/ticker/main/data/tickers.json
## 📄 Format
```json
{
  "lastUpdated": "2025-12-19T...",
  "count": 8000,
  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "isETF": false
    }
  ]
}
