"""
Environment Configuration Module

Centralized environment variable loading and configuration management
using python-dotenv for secure and flexible configuration.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Centralized environment configuration manager."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize environment configuration.

        Args:
            env_file: Optional path to .env file. If None, searches for .env in project root.
        """
        self._config = {}
        self._load_environment(env_file)
        self._validate_required_vars()

    def _load_environment(self, env_file: Optional[str] = None):
        """Load environment variables from .env file and system environment."""

        # Determine project root directory
        project_root = Path(__file__).parent.parent

        # Default .env file location
        if env_file is None:
            env_file = project_root / ".env"

        # Load .env file if it exists
        if Path(env_file).exists():
            load_dotenv(env_file, override=True)
            logger.info(f"Loaded environment from: {env_file}")
        else:
            logger.warning(f"Environment file not found: {env_file}")
            logger.info("Using system environment variables only")

        # Load all configuration with defaults
        self._load_aws_config()
        self._load_llm_config()
        self._load_api_config()
        self._load_system_config()
        self._load_agent_config()
        self._load_performance_config()
        self._load_cache_config()
        self._load_security_config()
        self._load_trading_config()
        self._load_technical_config()
        self._load_cli_config()

    def _load_aws_config(self):
        """Load AWS Bedrock configuration."""
        self._config.update({
            # AWS Configuration
            "aws_profile": os.getenv("AWS_PROFILE", "iris-aws"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        })

    def _load_llm_config(self):
        """Load LLM provider configuration."""
        self._config.update({
            # LLM Provider Settings
            "llm_provider": os.getenv("LLM_PROVIDER", "bedrock"),
            "quick_think_llm": os.getenv("QUICK_THINK_LLM", "claude-3-5-sonnet"),
            "deep_think_llm": os.getenv("DEEP_THINK_LLM", "claude-sonnet-4"),
            "quick_think_temperature": float(os.getenv("QUICK_THINK_TEMPERATURE", "0.1")),
            "deep_think_temperature": float(os.getenv("DEEP_THINK_TEMPERATURE", "0.1")),
            "quick_think_max_tokens": int(os.getenv("QUICK_THINK_MAX_TOKENS", "4000")),
            "deep_think_max_tokens": int(os.getenv("DEEP_THINK_MAX_TOKENS", "8000")),

            # Alternative Provider Settings
            "backend_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
        })

    def _load_api_config(self):
        """Load external API configuration."""
        self._config.update({
            # Financial Data APIs
            "finnhub_api_key": os.getenv("FINNHUB_API_KEY"),
            "alpha_vantage_api_key": os.getenv("ALPHA_VANTAGE_API_KEY"),
            "polygon_api_key": os.getenv("POLYGON_API_KEY"),
            "iex_cloud_api_key": os.getenv("IEX_CLOUD_API_KEY"),

            # Social Media & News APIs
            "reddit_client_id": os.getenv("REDDIT_CLIENT_ID"),
            "reddit_client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
            "reddit_user_agent": os.getenv("REDDIT_USER_AGENT", "TradingAgents/1.0"),
            "twitter_api_key": os.getenv("TWITTER_API_KEY"),
            "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
            "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
            "twitter_access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            "news_api_key": os.getenv("NEWS_API_KEY"),
        })

    def _load_system_config(self):
        """Load system and directory configuration."""
        project_root = Path(__file__).parent.parent

        self._config.update({
            # Project Directories
            "project_dir": str(project_root),
            "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
            "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", "./data"),
            "data_cache_dir": os.getenv("TRADINGAGENTS_CACHE_DIR",
                                      str(project_root / "tradingagents" / "dataflows" / "data_cache")),
            "logs_dir": os.getenv("TRADINGAGENTS_LOGS_DIR", "./logs"),

            # Debug and Development
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "enable_tracing": os.getenv("ENABLE_TRACING", "false").lower() == "true",
        })

    def _load_agent_config(self):
        """Load agent behavior configuration."""
        self._config.update({
            # Dynamic Model Selection
            "enable_dynamic_selection": os.getenv("ENABLE_DYNAMIC_SELECTION", "true").lower() == "true",
            "cost_optimization_enabled": os.getenv("COST_OPTIMIZATION_ENABLED", "true").lower() == "true",
            "performance_monitoring": os.getenv("PERFORMANCE_MONITORING", "true").lower() == "true",
            "model_selection_strategy": os.getenv("MODEL_SELECTION_STRATEGY", "adaptive"),

            # Agent Behavior
            "max_debate_rounds": int(os.getenv("MAX_DEBATE_ROUNDS", "1")),
            "max_risk_discuss_rounds": int(os.getenv("MAX_RISK_DISCUSS_ROUNDS", "1")),
            "max_recur_limit": int(os.getenv("MAX_RECUR_LIMIT", "100")),
            "online_tools": os.getenv("ONLINE_TOOLS", "true").lower() == "true",

            # Memory Configuration
            "memory_collection_size": int(os.getenv("MEMORY_COLLECTION_SIZE", "1000")),
            "memory_similarity_threshold": float(os.getenv("MEMORY_SIMILARITY_THRESHOLD", "0.7")),

            # Portfolio Analysis Configuration
            "portfolio_max_workers": int(os.getenv("PORTFOLIO_MAX_WORKERS", "2")),
            "portfolio_sequential": os.getenv("PORTFOLIO_SEQUENTIAL", "false").lower() == "true",
            "portfolio_timeout": int(os.getenv("PORTFOLIO_TIMEOUT", "300")),
            "enable_graceful_degradation": os.getenv("ENABLE_GRACEFUL_DEGRADATION", "true").lower() == "true",

            # Bedrock Rate Limiting - Optimized for real-time performance
            "bedrock_rate_limit": int(os.getenv("BEDROCK_RATE_LIMIT", "8")),
            "bedrock_retry_attempts": int(os.getenv("BEDROCK_RETRY_ATTEMPTS", "2")),  # Reduced from 3 to 2 for faster real-time response
            "bedrock_backoff_multiplier": float(os.getenv("BEDROCK_BACKOFF_MULTIPLIER", "1.5")),  # Reduced from 2 to 1.5 for faster recovery
            "bedrock_initial_delay": int(os.getenv("BEDROCK_INITIAL_DELAY", "1")),
        })

    def _load_performance_config(self):
        """Load performance and rate limiting configuration."""
        self._config.update({
            # Rate Limiting
            "finnhub_rate_limit": int(os.getenv("FINNHUB_RATE_LIMIT", "60")),
            "reddit_rate_limit": int(os.getenv("REDDIT_RATE_LIMIT", "100")),
            "google_news_rate_limit": int(os.getenv("GOOGLE_NEWS_RATE_LIMIT", "30")),

            # Request Configuration - Optimized for real-time performance
            "api_request_timeout": int(os.getenv("API_REQUEST_TIMEOUT", "30")),
            "llm_request_timeout": int(os.getenv("LLM_REQUEST_TIMEOUT", "120")),
            "max_retries": int(os.getenv("MAX_RETRIES", "2")),  # Reduced from 3 to 2 for faster real-time response
            "retry_delay": int(os.getenv("RETRY_DELAY", "1")),

            # Database Configuration
            "chroma_db_path": os.getenv("CHROMA_DB_PATH", "./chroma_db"),
            "chroma_collection_metadata": eval(os.getenv("CHROMA_COLLECTION_METADATA",
                                                       '{"hnsw:space": "cosine"}')),
        })

    def _load_cache_config(self):
        """Load cache policy and TTL configuration."""
        self._config.update({
            # Cache Policy Configuration
            "enable_smart_caching": os.getenv("ENABLE_SMART_CACHING", "true").lower() == "true",
            "cache_policy": os.getenv("CACHE_POLICY", "smart"),  # smart, aggressive, disabled

            # Cache TTL Settings (in minutes)
            "cache_ttl_live_data": int(os.getenv("CACHE_TTL_LIVE_DATA", "0")),         # No cache for live data
            "cache_ttl_intraday": int(os.getenv("CACHE_TTL_INTRADAY", "15")),          # 15 minutes
            "cache_ttl_historical": int(os.getenv("CACHE_TTL_HISTORICAL", "1440")),    # 24 hours
            "cache_ttl_static": int(os.getenv("CACHE_TTL_STATIC", "10080")),          # 7 days

            # Live Data Source Classification
            "live_data_sources": eval(os.getenv("LIVE_DATA_SOURCES",
                '["real_time_quote", "company_news", "insider_transactions", "market_indicators", '
                '"sector_performance", "stock_discussions", "market_sentiment", "earnings_data", '
                '"analyst_recommendations", "google_news"]')),

            # Intraday Data Sources (short TTL cache allowed)
            "intraday_data_sources": eval(os.getenv("INTRADAY_DATA_SOURCES",
                '["stock_price_current_day", "volume_current_day", "technical_indicators_current_day"]')),

            # Historical Data Sources (longer TTL cache allowed)
            "historical_data_sources": eval(os.getenv("HISTORICAL_DATA_SOURCES",
                '["stock_price_historical", "financial_statements", "dividend_history", "earnings_history"]')),

            # Cache Behavior Settings
            "force_live_current_day": os.getenv("FORCE_LIVE_CURRENT_DAY", "true").lower() == "true",
            "cache_bypass_trading_hours": os.getenv("CACHE_BYPASS_TRADING_HOURS", "true").lower() == "true",
            "cache_max_age_check": os.getenv("CACHE_MAX_AGE_CHECK", "true").lower() == "true",
        })

    def _load_security_config(self):
        """Load security and monitoring configuration."""
        self._config.update({
            # Monitoring
            "enable_usage_stats": os.getenv("ENABLE_USAGE_STATS", "true").lower() == "true",
            "enable_performance_logging": os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true",
            "enable_error_reporting": os.getenv("ENABLE_ERROR_REPORTING", "true").lower() == "true",

            # Privacy
            "anonymize_logs": os.getenv("ANONYMIZE_LOGS", "true").lower() == "true",
            "retain_sensitive_data": os.getenv("RETAIN_SENSITIVE_DATA", "false").lower() == "true",
        })

    def _load_trading_config(self):
        """Load trading system configuration."""
        self._config.update({
            # Trading Parameters
            "default_lookback_days": int(os.getenv("DEFAULT_LOOKBACK_DAYS", "30")),
            "default_confidence_threshold": float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.7")),

            # Risk Management
            "position_size_limit": float(os.getenv("POSITION_SIZE_LIMIT", "0.1")),
            "max_portfolio_risk": float(os.getenv("MAX_PORTFOLIO_RISK", "0.05")),

            # Backtesting
            "backtest_start_date": os.getenv("BACKTEST_START_DATE", "2023-01-01"),
            "backtest_end_date": os.getenv("BACKTEST_END_DATE", "2024-12-31"),
            "backtest_initial_capital": float(os.getenv("BACKTEST_INITIAL_CAPITAL", "100000")),
        })

    def _load_technical_config(self):
        """Load technical analysis configuration."""
        self._config.update({
            # Technical Analysis Features
            "enable_technical_analysis": os.getenv("ENABLE_TECHNICAL_ANALYSIS", "true").lower() == "true",

            # Technical Analysis Parameters
            "technical_min_periods": int(os.getenv("TECHNICAL_MIN_PERIODS", "20")),
            "technical_pattern_confidence_min": float(os.getenv("TECHNICAL_PATTERN_CONFIDENCE_MIN", "70")),
            "technical_volume_confirmation": os.getenv("TECHNICAL_VOLUME_CONFIRMATION", "true").lower() == "true",

            # Candlestick Pattern Settings
            "enable_candlestick_patterns": os.getenv("ENABLE_CANDLESTICK_PATTERNS", "true").lower() == "true",
            "candlestick_lookback_days": int(os.getenv("CANDLESTICK_LOOKBACK_DAYS", "30")),

            # Support/Resistance Analysis
            "enable_support_resistance": os.getenv("ENABLE_SUPPORT_RESISTANCE", "true").lower() == "true",
            "support_resistance_window": int(os.getenv("SUPPORT_RESISTANCE_WINDOW", "20")),
            "support_resistance_lookback": int(os.getenv("SUPPORT_RESISTANCE_LOOKBACK", "50")),

            # Fibonacci Analysis
            "enable_fibonacci_analysis": os.getenv("ENABLE_FIBONACCI_ANALYSIS", "true").lower() == "true",
            "fibonacci_trend_window": int(os.getenv("FIBONACCI_TREND_WINDOW", "50")),
            "fibonacci_proximity_threshold": float(os.getenv("FIBONACCI_PROXIMITY_THRESHOLD", "2.0")),

            # Technical Indicator Preferences
            "technical_rsi_period": int(os.getenv("TECHNICAL_RSI_PERIOD", "14")),
            "technical_macd_fast": int(os.getenv("TECHNICAL_MACD_FAST", "12")),
            "technical_macd_slow": int(os.getenv("TECHNICAL_MACD_SLOW", "26")),
            "technical_macd_signal": int(os.getenv("TECHNICAL_MACD_SIGNAL", "9")),
            "technical_bollinger_period": int(os.getenv("TECHNICAL_BOLLINGER_PERIOD", "20")),
            "technical_bollinger_std": float(os.getenv("TECHNICAL_BOLLINGER_STD", "2")),

            # Multi-timeframe Analysis
            "enable_multi_timeframe": os.getenv("ENABLE_MULTI_TIMEFRAME", "false").lower() == "true",
            "weekly_confirmation_required": os.getenv("WEEKLY_CONFIRMATION_REQUIRED", "false").lower() == "true",

            # Technical Analysis Cache Settings
            "technical_cache_enabled": os.getenv("TECHNICAL_CACHE_ENABLED", "true").lower() == "true",
            "technical_analysis_ttl": int(os.getenv("TECHNICAL_ANALYSIS_TTL", "900")),  # 15 minutes
        })

    def _load_cli_config(self):
        """Load CLI default preferences configuration."""
        self._config.update({
            # CLI Default Preferences
            "cli_auto_use_current_date": os.getenv("CLI_AUTO_USE_CURRENT_DATE", "true").lower() == "true",
            "cli_default_research_depth": os.getenv("CLI_DEFAULT_RESEARCH_DEPTH", "deep"),
            "cli_default_llm_provider": os.getenv("CLI_DEFAULT_LLM_PROVIDER", "bedrock"),
            "cli_default_shallow_thinker": os.getenv("CLI_DEFAULT_SHALLOW_THINKER", "claude-sonnet-4"),
            "cli_default_deep_thinker": os.getenv("CLI_DEFAULT_DEEP_THINKER", "claude-sonnet-4"),
            "cli_auto_select_all_analysts": os.getenv("CLI_AUTO_SELECT_ALL_ANALYSTS", "true").lower() == "true",
            "cli_default_mode": os.getenv("CLI_DEFAULT_MODE", "auto"),
        })

    def _validate_required_vars(self):
        """Validate required environment variables."""
        required_vars = {
            "aws_profile": "AWS_PROFILE",
            "aws_region": "AWS_REGION",
            "llm_provider": "LLM_PROVIDER",
        }

        missing_vars = []
        for config_key, env_var in required_vars.items():
            if not self._config.get(config_key):
                missing_vars.append(env_var)

        if missing_vars:
            logger.warning(f"Missing recommended environment variables: {missing_vars}")

        # Validate API keys for enabled features
        if self._config.get("online_tools"):
            if not self._config.get("finnhub_api_key"):
                logger.warning("FINNHUB_API_KEY not set - live financial data will be unavailable")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return self._config.copy()

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        self._config.update(updates)

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.get("debug_mode", False)

    def get_aws_config(self) -> Dict[str, str]:
        """Get AWS-specific configuration."""
        return {
            "aws_profile": self._config.get("aws_profile"),
            "aws_region": self._config.get("aws_region"),
            "aws_access_key_id": self._config.get("aws_access_key_id"),
            "aws_secret_access_key": self._config.get("aws_secret_access_key"),
        }

    def get_api_config(self) -> Dict[str, str]:
        """Get API keys configuration."""
        return {
            "finnhub_api_key": self._config.get("finnhub_api_key"),
            "reddit_client_id": self._config.get("reddit_client_id"),
            "reddit_client_secret": self._config.get("reddit_client_secret"),
            "reddit_user_agent": self._config.get("reddit_user_agent"),
            "openai_api_key": self._config.get("openai_api_key"),
            "anthropic_api_key": self._config.get("anthropic_api_key"),
            "google_api_key": self._config.get("google_api_key"),
        }

    def get_llm_config(self) -> Dict[str, Union[str, float, int]]:
        """Get LLM provider configuration."""
        return {
            "llm_provider": self._config.get("llm_provider"),
            "quick_think_llm": self._config.get("quick_think_llm"),
            "deep_think_llm": self._config.get("deep_think_llm"),
            "quick_think_temperature": self._config.get("quick_think_temperature"),
            "deep_think_temperature": self._config.get("deep_think_temperature"),
            "quick_think_max_tokens": self._config.get("quick_think_max_tokens"),
            "deep_think_max_tokens": self._config.get("deep_think_max_tokens"),
            "backend_url": self._config.get("backend_url"),
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache policy configuration."""
        return {
            "enable_smart_caching": self._config.get("enable_smart_caching"),
            "cache_policy": self._config.get("cache_policy"),
            "cache_ttl_live_data": self._config.get("cache_ttl_live_data"),
            "cache_ttl_intraday": self._config.get("cache_ttl_intraday"),
            "cache_ttl_historical": self._config.get("cache_ttl_historical"),
            "cache_ttl_static": self._config.get("cache_ttl_static"),
            "live_data_sources": self._config.get("live_data_sources"),
            "intraday_data_sources": self._config.get("intraday_data_sources"),
            "historical_data_sources": self._config.get("historical_data_sources"),
            "force_live_current_day": self._config.get("force_live_current_day"),
            "cache_bypass_trading_hours": self._config.get("cache_bypass_trading_hours"),
            "cache_max_age_check": self._config.get("cache_max_age_check"),
        }

    def get_cli_config(self) -> Dict[str, Any]:
        """Get CLI default preferences configuration."""
        return {
            "cli_auto_use_current_date": self._config.get("cli_auto_use_current_date"),
            "cli_default_research_depth": self._config.get("cli_default_research_depth"),
            "cli_default_llm_provider": self._config.get("cli_default_llm_provider"),
            "cli_default_shallow_thinker": self._config.get("cli_default_shallow_thinker"),
            "cli_default_deep_thinker": self._config.get("cli_default_deep_thinker"),
            "cli_auto_select_all_analysts": self._config.get("cli_auto_select_all_analysts"),
            "cli_default_mode": self._config.get("cli_default_mode"),
        }

    def __str__(self) -> str:
        """String representation of configuration (excluding sensitive data)."""
        safe_config = {}
        sensitive_keys = {"api_key", "secret", "token", "password", "key"}

        for key, value in self._config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_config[key] = "***HIDDEN***" if value else None
            else:
                safe_config[key] = value

        return f"EnvironmentConfig({safe_config})"


# Global configuration instance
_env_config = None

def get_env_config() -> EnvironmentConfig:
    """Get global environment configuration instance."""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfig()
    return _env_config

def reload_env_config(env_file: Optional[str] = None) -> EnvironmentConfig:
    """Reload environment configuration."""
    global _env_config
    _env_config = EnvironmentConfig(env_file)
    return _env_config