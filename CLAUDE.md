# TradingAgents - Claude Code Integration Guide

## Overview
TradingAgents is a sophisticated multi-agent trading system powered by AWS Bedrock Claude models. This system provides intelligent trading decisions through coordinated analysis from specialized AI agents, enhanced with real-time market data integration and dynamic model selection.

For comprehensive system architecture and multi-agent team structure details, see: https://deepwiki.com/TauricResearch/TradingAgents#multi-agent-team-structure

## Quick Start Commands

### Development & Testing
```bash
# Run all tests in proper order (recommended)
python scripts/run_tests.py

# Run specific test categories
python scripts/run_tests.py --category unit       # Fast component tests
python scripts/run_tests.py --category integration # Multi-component tests
python scripts/run_tests.py --category system     # Full system tests

# List available tests
python scripts/run_tests.py --list

# Test environment configuration (run this first!)
python tests/system/test_env_config.py

# Test complete system integration
python tests/system/test_bedrock_implementations.py

# Test enhanced Finnhub data integration
python tests/integration/test_enhanced_finnhub.py

# Test dynamic model selection
python tests/unit/test_dynamic_model_selection.py

# Test agent live data access
python tests/integration/test_agent_live_data.py

# Test Finnhub connection
python tests/unit/test_finnhub_connection.py

# Diagnose Bedrock embeddings system
python scripts/diagnose_bedrock_embeddings.py

# Test embedding system improvements
python scripts/test_embedding_improvements.py

# Test technical analysis functionality
python tests/unit/test_technical_patterns.py

# Test batch analysis retry mechanism
python tests/unit/test_batch_retry_simple.py
```

### Running the Trading System
```bash
# Analyze a single stock ticker
python -m cli.main analyze AAPL

# Analyze with specific date and output format
python -m cli.main analyze TSLA --date 2025-01-26 --output detailed

# Run batch analysis on portfolio
python -m cli.main batch

# Batch analysis with custom file and date
python -m cli.main batch --file my_portfolio.json --date 2025-01-28

# Run analysis programmatically
python -c "from tradingagents.graph.trading_graph import TradingAgentsGraph; ta = TradingAgentsGraph(); result = ta.propagate('AAPL', '2025-01-26')"
```

### Maintenance & Monitoring
```bash
# Check Bedrock model access
python -c "from tradingagents.llm_providers import get_configured_llms; from tradingagents.default_config import DEFAULT_CONFIG; get_configured_llms(DEFAULT_CONFIG)"

# Test embeddings quality
python -c "from tradingagents.bedrock_embeddings import BedrockEmbeddings; from tradingagents.default_config import DEFAULT_CONFIG; be = BedrockEmbeddings(DEFAULT_CONFIG); print(be.test_embedding_quality())"

# Monitor memory systems
python -c "from tradingagents.agents.utils.memory import FinancialSituationMemory; from tradingagents.default_config import DEFAULT_CONFIG; mem = FinancialSituationMemory('test', DEFAULT_CONFIG); print(mem.test_embedding_quality())"
```

## Repository Structure

The project is organized with a clean, logical structure:

```
TradingAgents/
├── tests/                          # Organized test suite
│   ├── unit/                       # Individual component tests
│   │   ├── test_dynamic_model_selection.py
│   │   ├── test_finnhub_connection.py
│   │   └── test_technical_patterns.py
│   ├── integration/                # Multi-component tests
│   │   ├── test_agent_live_data.py
│   │   └── test_enhanced_finnhub.py
│   └── system/                     # Full system tests
│       ├── test_bedrock_implementations.py
│       └── test_env_config.py
├── docs/                           # Project documentation
│   ├── LIVE_DATA_SETUP.md
│   └── README_STRUCTURE.md
├── scripts/                        # Utility scripts
│   ├── run_tests.py               # Comprehensive test runner
│   └── check_bedrock_models.py    # Model availability checker
├── tradingagents/                  # Core system code
└── CLAUDE.md                       # This file (always at root)
```

### Test Organization Benefits
- **🔒 Security**: No API keys in version control
- **📁 Organization**: Clear separation of concerns
- **🧪 Testing**: Proper test categorization and execution
- **📚 Documentation**: Centralized knowledge base
- **⚡ Performance**: Run only relevant test categories
- **👥 Collaboration**: Easy team navigation

## System Architecture

### Core Components
- **Multi-Agent Framework**: Coordinated specialists (Market, Technical, Social, News, Fundamentals analysts)
- **AWS Bedrock Integration**: Dynamic Claude model selection (Haiku/Sonnet/Opus)
- **Technical Analysis Engine**: TA-Lib powered candlestick patterns, support/resistance, Fibonacci analysis (NEW!)
- **Live Data Integration**: Real-time Finnhub, Google News, Reddit data
- **Memory Systems**: Bedrock-powered embeddings for experience retention
- **Risk Management**: Advanced controls with debate-driven decisions
- **Portfolio Management**: Comprehensive portfolio analysis and recommendations

### Agent Workflow
**Single Stock Analysis:**
1. **Data Collection**: Live market data from multiple sources
2. **Specialist Analysis**: Each agent analyzes their domain (Market, Technical, Social, News, Fundamentals)
3. **Technical Pattern Recognition**: Candlestick patterns, support/resistance levels, Fibonacci analysis
4. **Collaborative Debate**: Bull vs Bear researcher discussion with technical confirmation
5. **Risk Assessment**: Multi-perspective risk evaluation including technical stop-losses
6. **Final Decision**: Judge-mediated trading recommendation with technical timing signals

**Portfolio Analysis (NEW!):**
1. **Portfolio Loading**: Load positions and watchlist from `portfolio.json`
2. **Parallel Analysis**: Run TradingAgents analysis on all tickers simultaneously
3. **Risk Aggregation**: Calculate portfolio-wide risk metrics and concentration
4. **Position Recommendations**: Generate specific buy/sell/hold actions for existing positions
5. **Opportunity Analysis**: Evaluate watchlist stocks for new position entry
6. **Unified Report**: Combine individual analysis with portfolio-wide context

## Configuration

### Environment Configuration (.env file)
The system now uses a centralized `.env` file for all configuration. Copy `.env.example` to `.env` and configure your values:

```bash
# Copy example file and configure
cp .env.example .env

# Edit with your actual values
nano .env  # or your preferred editor
```

**Required Variables:**
- `AWS_PROFILE=iris-aws` (matches your Claude Code setup)
- `AWS_REGION=us-east-1`
- `LLM_PROVIDER=bedrock`
- `QUICK_THINK_LLM=claude-3-5-sonnet`
- `DEEP_THINK_LLM=claude-sonnet-4`
- `FINNHUB_API_KEY=d3adnfhr01qlsbrqvt60d3adnfhr01qlsbrqvt6g`

**Optional Variables:**
- `REDDIT_CLIENT_ID=your_client_id` (for social sentiment)
- `REDDIT_CLIENT_SECRET=your_client_secret`
- `ENABLE_DYNAMIC_SELECTION=true` (intelligent model selection)
- `COST_OPTIMIZATION_ENABLED=true` (cost management)

### Key Configuration Files
- `.env` - **Primary configuration file** (environment variables)
- `.env.example` - Template with all available options
- `tradingagents/env_config.py` - Environment configuration loader
- `tradingagents/default_config.py` - Main system configuration (now loads from .env)
- `cli/utils.py` - Interactive CLI settings
- `tradingagents/llm_providers.py` - Bedrock model configuration
- `tradingagents/dynamic_model_selector.py` - Intelligent model selection

### Configuration Management
```bash
# Test environment configuration
python test_env_config.py

# Validate .env file structure
python -c "from tradingagents.env_config import get_env_config; print(get_env_config())"

# Check specific configuration values
python -c "from tradingagents.default_config import DEFAULT_CONFIG; print(f'LLM: {DEFAULT_CONFIG[\"llm_provider\"]}, AWS: {DEFAULT_CONFIG[\"aws_profile\"]}')"

# Check smart caching configuration
python -c "from tradingagents.env_config import get_env_config; cache_config = get_env_config().get_cache_config(); print(f'Caching: {cache_config[\"cache_policy\"]}, TTL Live: {cache_config[\"cache_ttl_live_data\"]}min')"
```

### Smart Caching Configuration
The system uses intelligent caching to ensure time-sensitive trading data is always live:

```bash
# Cache policy settings in .env
ENABLE_SMART_CACHING=true         # Enable/disable smart caching
CACHE_POLICY=smart                # smart, aggressive, disabled
FORCE_LIVE_CURRENT_DAY=true      # Always live data for current day
CACHE_BYPASS_TRADING_HOURS=true  # Prefer live data during market hours

# TTL settings (in minutes)
CACHE_TTL_LIVE_DATA=0            # News, quotes, sentiment - never cached
CACHE_TTL_INTRADAY=15            # Current day prices - 15 min cache
CACHE_TTL_HISTORICAL=1440        # Historical data - 24 hour cache
CACHE_TTL_STATIC=10080          # Financial statements - 7 day cache
```

### Technical Analysis Configuration
The system includes comprehensive technical analysis capabilities with TA-Lib integration:

```bash
# Technical analysis settings in .env
ENABLE_TECHNICAL_ANALYSIS=true          # Enable/disable technical analysis
TECHNICAL_MIN_PERIODS=20                # Minimum data points for analysis
TECHNICAL_PATTERN_CONFIDENCE_MIN=70     # Minimum confidence for patterns (%)
TECHNICAL_VOLUME_CONFIRMATION=true      # Require volume confirmation

# Candlestick pattern settings
ENABLE_CANDLESTICK_PATTERNS=true
CANDLESTICK_LOOKBACK_DAYS=30           # Days of data for pattern detection

# Support/resistance analysis
ENABLE_SUPPORT_RESISTANCE=true
SUPPORT_RESISTANCE_WINDOW=20           # Rolling window for calculation
SUPPORT_RESISTANCE_LOOKBACK=50         # Days for analysis

# Fibonacci analysis
ENABLE_FIBONACCI_ANALYSIS=true
FIBONACCI_TREND_WINDOW=50              # Days to determine trend extremes
FIBONACCI_PROXIMITY_THRESHOLD=2.0      # Distance % to consider "near" level

# Technical indicator preferences
TECHNICAL_RSI_PERIOD=14
TECHNICAL_MACD_FAST=12
TECHNICAL_MACD_SLOW=26
TECHNICAL_BOLLINGER_PERIOD=20

# Cache settings for technical analysis
TECHNICAL_ANALYSIS_TTL=900             # 15 minutes cache
```

**Technical Analysis Features:**
- **55+ Candlestick Patterns**: Hammer, Doji, Engulfing, Morning/Evening Star, Three White Soldiers, etc.
- **Support & Resistance**: Dynamic level calculation with proximity alerts
- **Fibonacci Retracements**: Key levels (23.6%, 38.2%, 50%, 61.8%, 78.6%) with nearby zone detection
- **Technical Indicators**: RSI, MACD, Bollinger Bands, moving averages with configurable periods
- **Pattern Reliability Scoring**: Confidence ratings for each detected pattern
- **Multi-timeframe Capability**: Daily + weekly analysis support

**Installation Requirements:**
```bash
# Install technical analysis dependencies
brew install ta-lib                    # System dependency (macOS)
pip install TA-Lib                     # Python package

# Verify installation
python -c "import talib; print('TA-Lib installed successfully!')"
```

## Development Workflow

### Adding New Features
1. **Update Configuration**: Modify `default_config.py` for new settings
2. **Implement Components**: Add to appropriate `tradingagents/` subdirectory
3. **Create Tests**: Add test file following `test_*.py` pattern
4. **Update Integration**: Modify `trading_graph.py` for agent integration
5. **Test End-to-End**: Run comprehensive test suite

### Testing Strategy
The project uses a comprehensive three-tier testing approach:

- **Unit Tests** (`tests/unit/`): Individual component testing
  - `test_dynamic_model_selection.py` - Model selection logic
  - `test_finnhub_connection.py` - Finnhub API connectivity
  - `test_technical_patterns.py` - Technical analysis and pattern recognition

- **Integration Tests** (`tests/integration/`): Multi-component interaction testing
  - `test_agent_live_data.py` - Agent data integration
  - `test_enhanced_finnhub.py` - Enhanced Finnhub features

- **System Tests** (`tests/system/`): Full system comprehensive validation
  - `test_bedrock_implementations.py` - Complete Bedrock integration
  - `test_env_config.py` - Environment configuration system

Use `python scripts/run_tests.py` for organized test execution with proper sequencing and reporting.

### Common Development Tasks
```bash
# Add new data source
# 1. Implement in tradingagents/live_data_fetchers.py
# 2. Add tools to tradingagents/agents/utils/agent_utils.py
# 3. Update tool nodes in tradingagents/graph/trading_graph.py
# 4. Create unit test in tests/unit/ for API connectivity
# 5. Create integration test in tests/integration/ for agent usage
# 6. Run: python scripts/run_tests.py --category integration

# Modify agent behavior
# 1. Update agent files in tradingagents/agents/
# 2. Modify prompts and logic
# 3. Test with: python scripts/run_tests.py --category system
# 4. Update memory systems if needed
# 5. Validate with: python tests/system/test_bedrock_implementations.py

# Enhance model selection
# 1. Modify tradingagents/dynamic_model_selector.py
# 2. Update task complexity mappings
# 3. Test with: python tests/unit/test_dynamic_model_selection.py
# 4. Monitor cost and performance impact
# 5. Run full test suite: python scripts/run_tests.py

# Add new test
# 1. Determine category: unit (single component), integration (multi-component), or system (full system)
# 2. Create test_*.py file in appropriate tests/ subdirectory
# 3. Follow existing patterns in similar test files
# 4. Run: python scripts/run_tests.py --category [category]
```

## Production Deployment

### Performance Optimization
- **Model Selection**: Automatic Haiku/Sonnet/Opus assignment based on task complexity
- **Cost Management**: Dynamic cost optimization with performance monitoring
- **Smart Caching**: TTL-based caching with live data prioritization
  - Live data (news, quotes): No caching - always fresh
  - Intraday data: 15-minute cache for current day prices
  - Historical data: 24-hour cache for older market data
  - Static data: 7-day cache for financials and fundamentals
- **Memory Systems**: ChromaDB-based embeddings with efficient search
- **Intelligent Retry System**: Robust error handling with exponential backoff
  - **Throttling Recovery**: Automatic retry with 30s, 60s, 120s delays (±25% jitter)
  - **Adaptive Concurrency**: Reduces parallel workers by 50% when throttling detected
  - **Complete Data Collection**: Ensures all stocks analyzed before portfolio decisions
  - **Error Classification**: Distinguishes retryable (throttling) vs permanent (data) errors
  - **Timeout Protection**: 30-minute max analysis time with progress tracking

### Monitoring & Maintenance
- **Usage Statistics**: Built-in model usage and performance tracking
- **Data Quality**: Embedding quality assessment and monitoring
- **System Health**: Comprehensive error logging and graceful degradation
- **Performance Metrics**: Response times, accuracy tracking, cost optimization

### Scaling Considerations
- **Parallel Processing**: Multi-agent concurrent execution with adaptive throttling
- **Memory Management**: Efficient embedding storage and retrieval
- **API Rate Limits**: Intelligent retry with exponential backoff for throttling errors
- **Resource Optimization**: Dynamic model selection for cost efficiency
- **Batch Analysis Resilience**: Up to 3 retry attempts per stock with smart delays
- **Error Recovery**: Automatic retry queue management with completion tracking

## Troubleshooting

### Common Issues
```bash
# Bedrock Access Issues
# Check AWS credentials and model access permissions
aws bedrock list-foundation-models --region us-east-1

# Memory System Problems
# Test embeddings functionality
python -c "from tradingagents.bedrock_embeddings import BedrockEmbeddings; from tradingagents.default_config import DEFAULT_CONFIG; be = BedrockEmbeddings(DEFAULT_CONFIG); print(be.test_embedding_quality())"

# Data Source Failures
# Validate individual data connections
python tests/unit/test_finnhub_connection.py

# Agent Integration Issues
# Test complete system functionality
python tests/system/test_bedrock_implementations.py

# Environment Configuration Issues
# Validate .env configuration
python tests/system/test_env_config.py

# Run comprehensive diagnosis
python scripts/run_tests.py --category system
```

### Debug Mode
```bash
# Run with debug tracing
python -c "
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG)
result = ta.propagate('AAPL', '2025-01-26')
"
```

### Performance Tuning
- **Model Selection**: Adjust task complexity mappings in `dynamic_model_selector.py`
- **Memory Optimization**: Tune embedding dimensions and similarity thresholds
- **Data Integration**: Optimize API call patterns and caching strategies
- **Agent Coordination**: Fine-tune debate rounds and decision thresholds

## Integration Notes

### Claude Code Compatibility
- Uses identical AWS Bedrock configuration as your Claude Code setup
- Leverages `iris-aws` profile for seamless authentication
- Compatible with existing AWS IAM roles and permissions
- Maintains consistent model access patterns

### Data Sources
- **Live Integration**: Finnhub (financial data), Google News (web scraping), Reddit (social sentiment)
- **Smart Caching**: Time-sensitive data always live, historical data intelligently cached
- **Error Handling**: Graceful degradation with informative error messages
- **Performance**: Optimized API usage with TTL-based caching policies

### Security & Privacy
- **API Keys**: Hardcoded Finnhub key for local development (replace for production)
- **AWS Security**: Leverages existing Bedrock IAM roles and policies
- **Data Privacy**: No sensitive data stored permanently, memory systems use embeddings only
- **Error Logging**: Comprehensive but privacy-conscious error reporting

## Future Enhancements

### Planned Features
- **WebSocket Integration**: Real-time market data streaming
- **Advanced Risk Management**: Enhanced portfolio risk controls
- **Backtesting Framework**: Historical performance analysis
- **Performance Dashboard**: Real-time monitoring and analytics
- **Reddit API Integration**: Complete social sentiment analysis

### Extension Points
- **Custom Data Sources**: Easy integration of new financial APIs
- **Additional Models**: Support for other Bedrock models and providers
- **Agent Specialization**: New analyst types for specific markets or strategies
- **Risk Frameworks**: Advanced risk assessment methodologies
- **Deployment Options**: Cloud deployment and scaling configurations

## Portfolio Management (NEW!)

### Overview
The portfolio management system transforms TradingAgents from single-stock analysis to comprehensive portfolio management while maintaining the same high-quality individual stock analysis.

### Setup Portfolio
1. **Create Portfolio Configuration:**
   ```bash
   # Copy example to get started
   cp portfolio.example.json portfolio.json

   # Edit with your actual positions
   nano portfolio.json
   ```

2. **Portfolio Configuration Format:**
   ```json
   {
     "name": "My Trading Portfolio",
     "settings": {
       "cash_available": 25000.0,
       "max_position_pct": 0.15,    // 15% max single position
       "max_sector_pct": 0.40,      // 40% max sector exposure
       "stop_loss_pct": 0.08        // 8% stop loss threshold
     },
     "positions": [
       {
         "ticker": "AAPL",
         "shares": 100,
         "avg_cost": 150.25,
         "sector": "Technology",
         "notes": "Core holding"
       }
     ],
     "watchlist": [
       {
         "ticker": "MSFT",
         "target_allocation_pct": 10.0,
         "notes": "Waiting for entry"
       }
     ]
   }
   ```

### Daily Portfolio Workflow
```bash
# 1. Morning portfolio analysis
python -m cli.main batch

# 2. Review recommendations and execute trades

# 3. Update portfolio.json with new positions
# Edit file with actual shares and prices after trades

# 4. Run analysis again to verify portfolio health
python -m cli.main batch --format summary
```

### Portfolio Features

**🔍 Comprehensive Analysis:**
- Individual stock analysis for all positions + watchlist
- Portfolio-wide risk assessment
- Concentration and sector exposure monitoring
- Performance tracking with unrealized P&L

**📊 Risk Management:**
- Position size limits (default 15% max per stock)
- Sector concentration limits (default 40% max per sector)
- Cash allocation monitoring (5-25% recommended range)
- Stop-loss alerts at 8% threshold

**💡 Actionable Recommendations:**
- Specific share quantities for buy/sell decisions
- Priority-ranked action list
- Rebalancing recommendations for risk reduction
- New position sizing for watchlist opportunities

**📈 Output Formats:**
- **Detailed**: Full analysis with tables and individual stock breakdowns
- **Summary**: Quick overview with key metrics and priority actions

### Portfolio vs Single-Stock Analysis

| Feature | Single Stock | Portfolio |
|---------|-------------|-----------|
| Analysis Quality | ✅ Full TradingAgents depth | ✅ Same quality per stock |
| Risk Context | ❌ No portfolio awareness | ✅ Portfolio-wide risk management |
| Position Sizing | ❌ Generic recommendations | ✅ Specific share quantities |
| Concentration Risk | ❌ Not considered | ✅ Actively monitored |
| Execution Speed | ⚡ ~2-5 min per stock | ⚡ Parallel processing |
| Use Case | Daily stock picks | Complete portfolio management |

### Best Practices
- **Update Regularly**: Edit `portfolio.json` after executing trades
- **Monitor Alerts**: Pay attention to concentration risk warnings
- **Follow Priorities**: Execute high-priority actions first
- **Maintain Cash**: Keep 5-15% cash for opportunities
- **Diversify Sectors**: Avoid >40% in any single sector

---

## Support & Documentation

For additional help:
1. Review test files for usage examples
2. Check configuration files for settings options
3. Examine agent implementations for behavior customization
4. Test individual components before system integration
5. Monitor logs for performance and error analysis

The system is designed for extensibility and production use with comprehensive error handling, performance optimization, and intelligent model selection.