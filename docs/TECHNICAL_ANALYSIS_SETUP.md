# Technical Analysis Setup Guide

This guide covers the setup and usage of technical analysis features in TradingAgents, including K-line pattern detection, support/resistance analysis, and Fibonacci retracements.

## Overview

TradingAgents includes a comprehensive Technical Analyst agent that provides:

- **📈 Candlestick Pattern Detection**: 55+ patterns including Hammer, Doji, Engulfing, Morning Star, Evening Star, Three White Soldiers, etc.
- **🎯 Support & Resistance Analysis**: Dynamic level calculation based on current price action
- **📐 Fibonacci Retracement Analysis**: Key retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- **📊 Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages with momentum analysis
- **⚡ Live Data Integration**: Always uses real-time market data for time-sensitive analysis

## Installation Requirements

### Core Technical Analysis Engine: TA-Lib

TA-Lib is the industry-standard library for technical analysis and is **required** for technical analysis features.

#### macOS Installation (Recommended)
```bash
# Install TA-Lib system library via Homebrew
brew install ta-lib

# Install Python wrapper
pip install TA-Lib
```

#### Linux (Ubuntu/Debian) Installation
```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install build-essential wget

# Download and compile TA-Lib from source
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# Install Python wrapper
pip install TA-Lib
```

#### Windows Installation
```bash
# Option 1: Install via conda (recommended)
conda install -c conda-forge ta-lib

# Option 2: Download pre-compiled wheel
# Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# Download appropriate .whl file and install with:
# pip install TA_Lib-0.4.25-cp310-cp310-win_amd64.whl
```

### Optional Enhancement: pandas-ta

`pandas-ta` provides additional technical indicators but requires Python 3.12+:

```bash
# Only if using Python 3.12 or higher
pip install pandas-ta
```

> **Note**: pandas-ta is completely optional. TA-Lib provides all essential technical analysis functionality.

## Configuration

### Environment Variables

Technical analysis behavior can be configured via `.env` file:

```bash
# Technical Analysis Features
ENABLE_TECHNICAL_ANALYSIS=true

# Pattern Detection Settings
ENABLE_CANDLESTICK_PATTERNS=true
CANDLESTICK_LOOKBACK_DAYS=30
TECHNICAL_PATTERN_CONFIDENCE_MIN=70

# Support/Resistance Analysis
ENABLE_SUPPORT_RESISTANCE=true
SUPPORT_RESISTANCE_WINDOW=20
SUPPORT_RESISTANCE_LOOKBACK=50

# Fibonacci Analysis
ENABLE_FIBONACCI_ANALYSIS=true
FIBONACCI_TREND_WINDOW=50
FIBONACCI_PROXIMITY_THRESHOLD=2.0

# Technical Indicators
TECHNICAL_RSI_PERIOD=14
TECHNICAL_MACD_FAST=12
TECHNICAL_MACD_SLOW=26
TECHNICAL_MACD_SIGNAL=9
TECHNICAL_BOLLINGER_PERIOD=20
TECHNICAL_BOLLINGER_STD=2

# Live Data Settings (Technical analysis ALWAYS uses live data)
TECHNICAL_CACHE_ENABLED=true
TECHNICAL_ANALYSIS_TTL=900  # 15 minutes cache
```

## Usage Examples

### 1. Single Stock Technical Analysis

```bash
# Analyze AAPL with technical analysis included
python -m cli.main analyze AAPL --date 2025-01-28
```

### 2. Programmatic Usage

```python
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

# Initialize toolkit
toolkit = Toolkit(DEFAULT_CONFIG)

# Get comprehensive technical analysis
technical_report = toolkit.get_technical_analysis_report_online.invoke({
    'ticker': 'AAPL',
    'curr_date': '2025-01-28',
    'lookback_days': 50
})

# Get specific candlestick patterns
patterns = toolkit.get_candlestick_patterns_online.invoke({
    'ticker': 'AAPL',
    'curr_date': '2025-01-28',
    'lookback_days': 30
})

# Get support and resistance levels
support_resistance = toolkit.get_support_resistance_online.invoke({
    'ticker': 'AAPL',
    'curr_date': '2025-01-28',
    'lookback_days': 50
})

# Get Fibonacci analysis
fibonacci = toolkit.get_fibonacci_analysis_online.invoke({
    'ticker': 'AAPL',
    'curr_date': '2025-01-28',
    'trend_window': 50
})
```

### 3. Technical Analysis via TradingAgentsGraph

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create trading graph with technical analysis enabled
config = DEFAULT_CONFIG.copy()
config["analysts"] = ["market", "technical", "news", "fundamentals"]

ta_graph = TradingAgentsGraph(config=config)

# Run complete analysis including technical analysis
state, decision = ta_graph.propagate("AAPL", "2025-01-28")

# Technical analysis results will be in state["technical_report"]
print(state["technical_report"])
```

## Technical Analysis Features

### Candlestick Pattern Detection

The system detects 55+ candlestick patterns using TA-Lib:

**Reversal Patterns:**
- Hammer, Hanging Man
- Doji, Dragonfly Doji, Gravestone Doji
- Engulfing (Bullish/Bearish)
- Morning Star, Evening Star
- Piercing Pattern, Dark Cloud Cover
- Harami, Harami Cross

**Continuation Patterns:**
- Three White Soldiers, Three Black Crows
- Rising/Falling Three Methods
- Mat Hold, Breakaway
- Ladder Bottom/Top

Each pattern includes:
- Pattern name and type (bullish/bearish/neutral)
- Reliability percentage (based on historical success rate)
- Days since detection
- Trading implications and suggested actions

### Support and Resistance Analysis

Dynamic calculation of key price levels:

- **Support Level**: Price level where buying interest is expected
- **Resistance Level**: Price level where selling pressure may emerge
- **Current Price Position**: Relative to support/resistance levels
- **Distance Percentages**: How far current price is from key levels
- **Trading Range**: Whether price is in normal trading range

### Fibonacci Retracement Analysis

Calculates key retracement levels:

- **Trend Identification**: Determines recent high and low points
- **Retracement Levels**: 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
- **Current Price Analysis**: Which Fibonacci level is closest
- **Proximity Alerts**: When price approaches key Fibonacci levels

### Technical Indicators

Comprehensive indicator analysis:

- **RSI (Relative Strength Index)**: Overbought/oversold conditions
- **MACD**: Trend momentum and crossover signals
- **Bollinger Bands**: Volatility and mean reversion signals
- **Moving Averages**: Trend direction (20, 50, 200 SMA/EMA)
- **Volume Analysis**: Confirmation of price movements

## Live Data Priority

**Important**: Technical analysis in TradingAgents **ALWAYS** uses live market data. There is no offline mode for technical analysis because:

- K-line patterns change throughout the trading day
- Support/resistance levels shift with intraday price action
- Technical indicators update continuously
- Volume patterns provide real-time confirmation

The system prioritizes live data to ensure technical analysis reflects current market conditions for accurate trading signals.

## Troubleshooting

### Common Installation Issues

**TA-Lib compilation errors on Linux:**
```bash
# Install additional dependencies
sudo apt-get install python3-dev python3-pip
sudo apt-get install build-essential autoconf libtool pkg-config
```

**TA-Lib not found error:**
```bash
# Verify TA-Lib installation
python -c "import talib; print('TA-Lib installed successfully')"

# If error persists, try reinstalling
pip uninstall TA-Lib
pip install --no-cache-dir TA-Lib
```

**pandas-ta version conflicts:**
```bash
# Check Python version (pandas-ta requires 3.12+)
python --version

# For Python < 3.12, skip pandas-ta (TA-Lib is sufficient)
# Remove from requirements if causing issues:
# Comment out pandas-ta in requirements.txt
```

### Performance Optimization

**For faster technical analysis:**
- Reduce `lookback_days` for quicker pattern detection
- Increase `TECHNICAL_ANALYSIS_TTL` for more caching
- Use smaller `FIBONACCI_TREND_WINDOW` for trend analysis

**For more accurate analysis:**
- Increase `lookback_days` for better pattern context
- Set `TECHNICAL_VOLUME_CONFIRMATION=true` for volume validation
- Use larger datasets with `SUPPORT_RESISTANCE_LOOKBACK=100`

## Testing Technical Analysis

Verify technical analysis is working:

```bash
# Test TA-Lib installation
python -c "
import talib
print('✅ TA-Lib available')
from tradingagents.technical_patterns import TechnicalPatternAnalyzer
print('✅ Technical Pattern Analyzer ready')
"

# Test technical analysis tools
python -c "
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

toolkit = Toolkit(DEFAULT_CONFIG)
result = toolkit.get_technical_analysis_report_online.invoke({
    'ticker': 'AAPL', 'curr_date': '2025-01-28', 'lookback_days': 30
})
print(f'✅ Technical analysis working: {len(result)} characters')
"
```

## Support

For technical analysis issues:
1. Ensure TA-Lib is properly installed for your platform
2. Check that FINNHUB_API_KEY is set for live data access
3. Verify AWS Bedrock access for the Technical Analyst agent
4. Review logs for specific error messages

The technical analysis system is designed to work seamlessly with the multi-agent framework while providing comprehensive, time-sensitive market analysis.