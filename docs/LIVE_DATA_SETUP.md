# Live Data API Setup Guide

Your TradingAgents system now supports **live data** from Finnhub and Reddit! Here's how to set it up:

## 🔑 Required API Keys

### 1. Finnhub API (Financial News & Data)

✅ **Already configured!** The Finnhub API key is hardcoded in the project for local use.

No setup needed - your system will automatically connect to live Finnhub data.

### 2. Reddit API (Social Sentiment)

**Create Reddit App:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Note down your `client_id` and `client_secret`

**Set environment variables:**
```bash
export REDDIT_CLIENT_ID=your_reddit_client_id
export REDDIT_CLIENT_SECRET=your_reddit_client_secret
export REDDIT_USER_AGENT=TradingAgents/1.0
```

## 📊 What Live Data You'll Get

### 🏢 **Finnhub Live Data:**
- **Company News**: Latest financial news articles
- **Insider Transactions**: Real-time insider trading data
- **Market Data**: Live financial metrics

### 💭 **Reddit Live Data:**
- **Stock Discussions**: Live discussions about specific stocks
- **Market Sentiment**: General market mood and trends
- **Social Trends**: What retail investors are talking about

### 🌐 **Google News** (Already Working):
- **Live News Scraping**: Real-time news articles
- **Date-filtered Results**: News from specific time periods

## 🚀 How to Use

**Your agents now automatically have access to these live tools:**

### Social Analyst:
- `get_reddit_stock_discussions_live` - Live Reddit stock discussions
- `get_stock_news_bedrock` - AI-powered sentiment analysis

### News Analyst:
- `get_finnhub_news_live` - Live Finnhub news
- `get_reddit_market_sentiment_live` - Live Reddit market sentiment
- `get_google_news` - Live Google News scraping

### Fundamentals Analyst:
- `get_finnhub_insider_transactions_live` - Live insider trading data
- `get_fundamentals_bedrock` - AI-powered fundamental analysis

## ⚙️ Configuration

**Add to your shell profile (.bashrc, .zshrc, etc.):**
```bash
# Finnhub API (already hardcoded, no setup needed)

# Reddit API (optional - only if you want Reddit data)
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
export REDDIT_USER_AGENT=TradingAgents/1.0
```

**Then reload your shell:**
```bash
source ~/.zshrc  # or ~/.bashrc
```

## 🔄 Fallback System

**Don't worry if you don't set up all APIs immediately:**

- ✅ **Google News**: Always works (no API key needed)
- 🔑 **Finnhub**: Falls back to cached data or returns helpful messages
- 🔑 **Reddit**: Falls back to cached data or returns helpful messages
- 🧠 **Bedrock Analysis**: Always works with your AWS setup

**Your system gracefully handles missing API keys and still provides valuable analysis!**

## 🧪 Test Live Data

**Run this to test your setup:**
```bash
python -c "
from tradingagents.live_data_fetchers import live_finnhub, live_reddit
print('Testing Finnhub:', live_finnhub.get_company_news('AAPL', '2024-01-01', '2024-01-07')[:100])
print('Testing Reddit:', live_reddit.get_stock_discussions('AAPL')[:100])
"
```

## 🎯 Result

**With all APIs configured, your agents will have access to:**
- 🟢 **Live Google News** (web scraping)
- 🟢 **Live Finnhub Financial Data** (API)
- 🟢 **Live Reddit Sentiment** (API)
- 🟢 **Claude Analysis** (AWS Bedrock)

**= Complete real-time market intelligence! 🚀**