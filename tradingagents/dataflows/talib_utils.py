"""
Technical Analysis Utilities for TradingAgents DataFlows

This module provides interface functions for technical analysis integration
with the existing dataflow system. It uses the technical_patterns module
and follows the same caching and data fetching patterns as other utils.
"""

import pandas as pd
import yfinance as yf
from typing import Annotated, Dict, Any, Optional
import os
from datetime import datetime, timedelta
from ..default_config import DEFAULT_CONFIG
from .cache_utils import get_smart_cache, create_cache_key
from ..technical_patterns import TechnicalPatternAnalyzer, analyze_stock_patterns


def get_config():
    """Get configuration - simplified for Bedrock-only architecture."""
    return DEFAULT_CONFIG.copy()


class TechnicalAnalysisUtils:
    """Utility class for technical analysis integration with dataflows."""

    @staticmethod
    def get_technical_analysis(
        symbol: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
        lookback_days: Annotated[int, "how many days of data to analyze"] = 100,
        online: Annotated[bool, "whether to use online or offline data"] = True,
        data_dir: Annotated[str, "directory for offline data"] = None
    ) -> str:
        """
        Perform comprehensive technical analysis on a stock.

        Args:
            symbol: Ticker symbol of the company
            curr_date: Current date for analysis
            lookback_days: Number of days of historical data to analyze
            online: Whether to fetch data online or use offline files
            data_dir: Directory for offline data files

        Returns:
            Formatted technical analysis report
        """
        try:
            # Get price data
            data = TechnicalAnalysisUtils._get_price_data(
                symbol, curr_date, lookback_days, online, data_dir
            )

            if data is None or data.empty:
                return f"Technical Analysis Error: No price data available for {symbol}"

            # Configure technical analysis
            config = {
                'min_periods': 20,
                'volume_confirmation': True
            }

            # Generate technical analysis report
            report = analyze_stock_patterns(symbol, data, config)
            return report

        except Exception as e:
            return f"Technical Analysis Error for {symbol}: {str(e)}"

    @staticmethod
    def get_candlestick_patterns(
        symbol: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
        lookback_days: Annotated[int, "days of data for pattern analysis"] = 30,
        online: Annotated[bool, "whether to use online data"] = True
    ) -> str:
        """
        Detect candlestick patterns specifically.

        Args:
            symbol: Ticker symbol
            curr_date: Current analysis date
            lookback_days: Days of data to analyze
            online: Use online data fetching

        Returns:
            Formatted candlestick pattern report
        """
        try:
            data = TechnicalAnalysisUtils._get_price_data(
                symbol, curr_date, lookback_days, online
            )

            if data is None or data.empty:
                return f"Pattern Analysis Error: No data available for {symbol}"

            analyzer = TechnicalPatternAnalyzer()
            patterns = analyzer.detect_candlestick_patterns(data)

            if 'error' in patterns:
                return f"Pattern Analysis Error for {symbol}: {patterns['error']}"

            # Format pattern report
            report = f"# Candlestick Pattern Analysis: {symbol}\n\n"

            detected = patterns.get('patterns_detected', {})
            if detected:
                report += f"**Patterns Detected:** {len(detected)}\n\n"

                # Group by pattern type
                reversal_patterns = []
                continuation_patterns = []
                indecision_patterns = []

                for pattern_name, pattern_data in detected.items():
                    pattern_info = {
                        'name': pattern_name,
                        'direction': pattern_data['direction'],
                        'reliability': pattern_data['reliability'],
                        'days_ago': pattern_data['days_ago']
                    }

                    if 'reversal' in pattern_data['type']:
                        reversal_patterns.append(pattern_info)
                    elif 'continuation' in pattern_data['type']:
                        continuation_patterns.append(pattern_info)
                    else:
                        indecision_patterns.append(pattern_info)

                # Add pattern sections
                if reversal_patterns:
                    report += "## Reversal Patterns\n"
                    for p in reversal_patterns:
                        report += f"- **{p['name']}** ({p['direction']}) - {p['reliability']}% reliability, {p['days_ago']} days ago\n"
                    report += "\n"

                if continuation_patterns:
                    report += "## Continuation Patterns\n"
                    for p in continuation_patterns:
                        report += f"- **{p['name']}** ({p['direction']}) - {p['reliability']}% reliability, {p['days_ago']} days ago\n"
                    report += "\n"

                if indecision_patterns:
                    report += "## Indecision Patterns\n"
                    for p in indecision_patterns:
                        report += f"- **{p['name']}** ({p['direction']}) - {p['reliability']}% reliability, {p['days_ago']} days ago\n"
                    report += "\n"

            else:
                report += "**No significant candlestick patterns detected in recent trading.**\n\n"

            report += f"*Analysis date: {patterns.get('analysis_date', curr_date)}*"
            return report

        except Exception as e:
            return f"Candlestick Pattern Error for {symbol}: {str(e)}"

    @staticmethod
    def get_support_resistance_levels(
        symbol: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
        lookback_days: Annotated[int, "days for support/resistance calculation"] = 50,
        online: Annotated[bool, "whether to use online data"] = True
    ) -> str:
        """
        Calculate support and resistance levels.

        Args:
            symbol: Ticker symbol
            curr_date: Current analysis date
            lookback_days: Days of data for level calculation
            online: Use online data fetching

        Returns:
            Formatted support/resistance report
        """
        try:
            data = TechnicalAnalysisUtils._get_price_data(
                symbol, curr_date, lookback_days, online
            )

            if data is None or data.empty:
                return f"Support/Resistance Error: No data available for {symbol}"

            analyzer = TechnicalPatternAnalyzer()
            sr_levels = analyzer.analyze_support_resistance(data, window=20)

            if 'error' in sr_levels:
                return f"Support/Resistance Error for {symbol}: {sr_levels['error']}"

            # Format report
            report = f"# Support & Resistance Analysis: {symbol}\n\n"
            report += f"**Current Price:** ${sr_levels['current_price']}\n\n"

            report += f"**Support Level:** ${sr_levels['support_level']}\n"
            report += f"- Distance: {sr_levels['support_distance_pct']}% below current price\n"

            report += f"\n**Resistance Level:** ${sr_levels['resistance_level']}\n"
            report += f"- Distance: {sr_levels['resistance_distance_pct']}% above current price\n\n"

            # Trading implications
            report += "## Trading Implications\n"
            if sr_levels['support_distance_pct'] <= 2:
                report += "- 🟢 **Near Support Level** - Potential buying opportunity\n"
            elif sr_levels['resistance_distance_pct'] <= 2:
                report += "- 🔴 **Near Resistance Level** - Potential selling opportunity\n"
            elif sr_levels['in_range']:
                report += "- 📊 **Within Trading Range** - Monitor for breakout\n"
            else:
                report += "- ⚠️ **Outside Trading Range** - Potential trend continuation\n"

            return report

        except Exception as e:
            return f"Support/Resistance Error for {symbol}: {str(e)}"

    @staticmethod
    def get_fibonacci_analysis(
        symbol: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
        trend_window: Annotated[int, "days to determine trend high/low"] = 50,
        online: Annotated[bool, "whether to use online data"] = True
    ) -> str:
        """
        Calculate Fibonacci retracement levels.

        Args:
            symbol: Ticker symbol
            curr_date: Current analysis date
            trend_window: Days to determine trend extremes
            online: Use online data fetching

        Returns:
            Formatted Fibonacci analysis report
        """
        try:
            data = TechnicalAnalysisUtils._get_price_data(
                symbol, curr_date, trend_window + 10, online
            )

            if data is None or data.empty:
                return f"Fibonacci Analysis Error: No data available for {symbol}"

            analyzer = TechnicalPatternAnalyzer()
            fib_analysis = analyzer.calculate_fibonacci_levels(data, trend_window)

            if 'error' in fib_analysis:
                return f"Fibonacci Analysis Error for {symbol}: {fib_analysis['error']}"

            # Format report
            report = f"# Fibonacci Retracement Analysis: {symbol}\n\n"

            report += f"**Current Price:** ${fib_analysis['current_price']}\n"
            report += f"**Trend High:** ${fib_analysis['trend_high']}\n"
            report += f"**Trend Low:** ${fib_analysis['trend_low']}\n\n"

            report += "## Fibonacci Levels\n"
            for level_name, level_price in fib_analysis['fibonacci_levels'].items():
                report += f"- {level_name}: ${level_price}\n"

            # Nearby levels
            nearby = fib_analysis.get('nearby_levels', {})
            if nearby:
                report += "\n## Key Levels Near Current Price\n"
                for level_name, level_data in nearby.items():
                    report += f"- **{level_name}**: ${level_data['price']} ({level_data['distance_pct']}% away)\n"

                report += "\n🎯 **Trading Note:** Price is near key Fibonacci levels - watch for potential reversals or continuations.\n"

            return report

        except Exception as e:
            return f"Fibonacci Analysis Error for {symbol}: {str(e)}"

    @staticmethod
    def _get_price_data(
        symbol: str,
        curr_date: str,
        lookback_days: int,
        online: bool = True,
        data_dir: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Get price data with smart caching, similar to stockstats_utils pattern.

        Args:
            symbol: Stock ticker
            curr_date: Current date
            lookback_days: Days of historical data needed
            online: Use online fetching
            data_dir: Directory for offline data

        Returns:
            DataFrame with OHLCV data or None if error
        """
        data = None

        if not online and data_dir:
            # Try offline data
            try:
                file_path = os.path.join(
                    data_dir,
                    f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv"
                )
                data = pd.read_csv(file_path)
            except FileNotFoundError:
                raise Exception("Technical analysis fail: Yahoo Finance data not fetched yet!")

        else:
            # Online data fetching with smart caching
            today_date = pd.Timestamp.today()
            curr_date_dt = pd.to_datetime(curr_date)

            # Calculate date range
            start_date = curr_date_dt - pd.DateOffset(days=lookback_days)
            end_date = min(today_date, curr_date_dt + pd.DateOffset(days=1))

            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            curr_date_str = curr_date_dt.strftime("%Y-%m-%d")

            # Determine if this is time-sensitive data
            is_current_day = curr_date_dt.date() == today_date.date()
            data_source = "technical_analysis_current" if is_current_day else "technical_analysis_historical"

            # Create cache key
            cache_key = create_cache_key(
                data_source=data_source,
                symbol=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                lookback_days=lookback_days
            )

            # Initialize smart cache
            smart_cache = get_smart_cache()

            # Check cache for historical data only
            use_cache = False
            if not is_current_day:
                use_cache = smart_cache.should_use_cache(
                    data_source=data_source,
                    date_str=curr_date_str,
                    cache_key=cache_key
                )

            if use_cache:
                cached_data = smart_cache.get_cached_data(cache_key)
                if cached_data is not None:
                    try:
                        import io
                        data = pd.read_csv(io.StringIO(cached_data))
                        data["Date"] = pd.to_datetime(data["Date"])
                        print(f"🔄 Using cached technical analysis data for {symbol}")
                    except Exception as e:
                        print(f"⚠️ Failed to load cached technical data: {e}")
                        data = None

            # Fetch fresh data if no valid cache
            if data is None:
                data_type = "LIVE" if is_current_day else "historical"
                print(f"🔴 Fetching {data_type} technical analysis data for {symbol}")

                data = yf.download(
                    symbol,
                    start=start_date_str,
                    end=end_date_str,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True
                )
                data = data.reset_index()

                # Cache historical data only
                if not is_current_day and not data.empty:
                    try:
                        csv_data = data.to_csv(index=False)
                        success = smart_cache.set_cached_data(
                            cache_key=cache_key,
                            data=csv_data,
                            data_source=data_source,
                            date_str=curr_date_str
                        )
                        if not success:
                            print(f"⚠️ Technical analysis cache storage rejected for {symbol}")
                    except Exception as e:
                        print(f"⚠️ Failed to cache technical analysis data: {e}")

        return data


# Interface functions for integration with existing system
def get_technical_analysis_report(
    symbol: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
    lookback_days: Annotated[int, "days of data to analyze"] = 100,
    online: Annotated[bool, "whether to use online data"] = True
) -> str:
    """
    Main interface function for technical analysis reports.
    """
    return TechnicalAnalysisUtils.get_technical_analysis(
        symbol, curr_date, lookback_days, online
    )


def get_candlestick_patterns_report(
    symbol: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
    lookback_days: Annotated[int, "days of data for pattern analysis"] = 30,
    online: Annotated[bool, "whether to use online data"] = True
) -> str:
    """
    Interface function for candlestick pattern analysis.
    """
    return TechnicalAnalysisUtils.get_candlestick_patterns(
        symbol, curr_date, lookback_days, online
    )


def get_support_resistance_report(
    symbol: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
    lookback_days: Annotated[int, "days for level calculation"] = 50,
    online: Annotated[bool, "whether to use online data"] = True
) -> str:
    """
    Interface function for support/resistance analysis.
    """
    return TechnicalAnalysisUtils.get_support_resistance_levels(
        symbol, curr_date, lookback_days, online
    )


def get_fibonacci_levels_report(
    symbol: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[str, "current date for analysis, YYYY-mm-dd"],
    trend_window: Annotated[int, "days to determine trend extremes"] = 50,
    online: Annotated[bool, "whether to use online data"] = True
) -> str:
    """
    Interface function for Fibonacci retracement analysis.
    """
    return TechnicalAnalysisUtils.get_fibonacci_analysis(
        symbol, curr_date, trend_window, online
    )