"""
Technical Analysis Pattern Recognition Module

This module provides comprehensive candlestick pattern detection and technical analysis
using TA-Lib for the TradingAgents system. It focuses on reliable patterns suitable
for daily trading decisions and provides confidence scoring for each pattern.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    warnings.warn("TA-Lib not available. Install with: pip install TA-Lib")

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    # pandas-ta is optional - TA-Lib provides core technical analysis functionality


class TechnicalPatternAnalyzer:
    """
    Comprehensive technical pattern analyzer using TA-Lib and pandas-ta.
    Focuses on candlestick patterns, trend analysis, and signal generation.
    """

    # Most reliable candlestick patterns for daily trading
    RELIABLE_PATTERNS = {
        'reversal': {
            'CDLHAMMER': {'name': 'Hammer', 'strength': 85, 'type': 'bullish_reversal'},
            'CDLHANGINGMAN': {'name': 'Hanging Man', 'strength': 75, 'type': 'bearish_reversal'},
            'CDLDOJI': {'name': 'Doji', 'strength': 70, 'type': 'neutral_reversal'},
            'CDLENGULFING': {'name': 'Engulfing Pattern', 'strength': 90, 'type': 'reversal'},
            'CDLMORNINGSTAR': {'name': 'Morning Star', 'strength': 95, 'type': 'bullish_reversal'},
            'CDLEVENINGSTAR': {'name': 'Evening Star', 'strength': 95, 'type': 'bearish_reversal'},
            'CDLPIERCING': {'name': 'Piercing Pattern', 'strength': 80, 'type': 'bullish_reversal'},
            'CDLDARKCLOUDCOVER': {'name': 'Dark Cloud Cover', 'strength': 80, 'type': 'bearish_reversal'},
            'CDLHARAMI': {'name': 'Harami', 'strength': 75, 'type': 'reversal'},
            'CDLINVERTEDHAMMER': {'name': 'Inverted Hammer', 'strength': 70, 'type': 'bullish_reversal'},
            'CDLSHOOTINGSTAR': {'name': 'Shooting Star', 'strength': 75, 'type': 'bearish_reversal'},
        },
        'continuation': {
            'CDL3WHITESOLDIERS': {'name': 'Three White Soldiers', 'strength': 90, 'type': 'bullish_continuation'},
            'CDL3BLACKCROWS': {'name': 'Three Black Crows', 'strength': 90, 'type': 'bearish_continuation'},
            'CDLRISEFALL3METHODS': {'name': 'Rising Three Methods', 'strength': 85, 'type': 'continuation'},
            'CDLSEPARATINGLINES': {'name': 'Separating Lines', 'strength': 70, 'type': 'continuation'},
        },
        'indecision': {
            'CDLSPINNINGTOP': {'name': 'Spinning Top', 'strength': 60, 'type': 'indecision'},
            'CDLDOJISTAR': {'name': 'Doji Star', 'strength': 75, 'type': 'indecision'},
            'CDLGRAVESTONEDOJI': {'name': 'Gravestone Doji', 'strength': 80, 'type': 'bearish_indecision'},
            'CDLDRAGONFLYDOJI': {'name': 'Dragonfly Doji', 'strength': 80, 'type': 'bullish_indecision'},
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Technical Pattern Analyzer.

        Args:
            config: Configuration dictionary with analysis parameters
        """
        self.config = config or {}
        self.min_periods = self.config.get('min_periods', 20)
        self.volume_confirmation = self.config.get('volume_confirmation', True)

        if not TALIB_AVAILABLE:
            raise ImportError("TA-Lib is required for pattern analysis. Install with: pip install TA-Lib")

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare OHLCV data for technical analysis.

        Args:
            data: DataFrame with OHLCV columns

        Returns:
            Cleaned and prepared DataFrame
        """
        # Standardize column names
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
            'Adj Close': 'adj_close'
        }

        df = data.copy()
        df = df.rename(columns=column_mapping)

        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Use adjusted close if available, otherwise regular close
        if 'adj_close' in df.columns:
            df['close'] = df['adj_close']

        # Fill missing volume with 0
        if 'volume' not in df.columns:
            df['volume'] = 0

        # Convert to float and handle missing values
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Forward fill missing values (max 3 consecutive)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].ffill(limit=3)

        # Remove rows with still missing values
        df = df.dropna(subset=['open', 'high', 'low', 'close'])

        return df

    def detect_candlestick_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect all supported candlestick patterns in the data.

        Args:
            data: Prepared OHLCV DataFrame

        Returns:
            Dictionary with pattern detection results
        """
        if len(data) < self.min_periods:
            return {'error': f'Insufficient data. Need at least {self.min_periods} periods.'}

        df = self.prepare_data(data)

        # Convert to numpy arrays for TA-Lib
        open_prices = df['open'].values
        high_prices = df['high'].values
        low_prices = df['low'].values
        close_prices = df['close'].values
        volumes = df['volume'].values

        detected_patterns = {}
        pattern_signals = {}

        # Detect all patterns from our reliable patterns dictionary
        all_patterns = {}
        for category in self.RELIABLE_PATTERNS:
            all_patterns.update(self.RELIABLE_PATTERNS[category])

        for pattern_func, pattern_info in all_patterns.items():
            try:
                # Call TA-Lib pattern function
                pattern_result = getattr(talib, pattern_func)(open_prices, high_prices, low_prices, close_prices)

                # Check for recent patterns (last 5 days)
                recent_signals = pattern_result[-5:]
                if any(signal != 0 for signal in recent_signals):
                    # Find the most recent non-zero signal
                    for i in range(len(recent_signals) - 1, -1, -1):
                        if recent_signals[i] != 0:
                            signal_strength = abs(recent_signals[i])
                            signal_direction = 'bullish' if recent_signals[i] > 0 else 'bearish'

                            detected_patterns[pattern_info['name']] = {
                                'signal_strength': signal_strength,
                                'direction': signal_direction,
                                'reliability': pattern_info['strength'],
                                'type': pattern_info['type'],
                                'days_ago': i,
                                'pattern_code': pattern_func
                            }
                            break

            except Exception as e:
                print(f"Error detecting pattern {pattern_func}: {e}")

        return {
            'patterns_detected': detected_patterns,
            'total_patterns': len(detected_patterns),
            'analysis_date': data.index[-1] if hasattr(data, 'index') else datetime.now().strftime('%Y-%m-%d')
        }

    def analyze_support_resistance(self, data: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        Calculate dynamic support and resistance levels.

        Args:
            data: OHLCV DataFrame
            window: Lookback window for calculations

        Returns:
            Dictionary with support/resistance levels
        """
        df = self.prepare_data(data)

        if len(df) < window:
            return {'error': 'Insufficient data for support/resistance analysis'}

        # Calculate pivot points using rolling windows
        high_prices = df['high']
        low_prices = df['low']
        close_prices = df['close']

        # Support: Lowest low in the window
        support = low_prices.rolling(window=window).min().iloc[-1]

        # Resistance: Highest high in the window
        resistance = high_prices.rolling(window=window).max().iloc[-1]

        # Current price
        current_price = close_prices.iloc[-1]

        # Calculate distance to levels as percentages
        support_distance = ((current_price - support) / current_price) * 100
        resistance_distance = ((resistance - current_price) / current_price) * 100

        return {
            'support_level': round(support, 2),
            'resistance_level': round(resistance, 2),
            'current_price': round(current_price, 2),
            'support_distance_pct': round(support_distance, 2),
            'resistance_distance_pct': round(resistance_distance, 2),
            'in_range': support < current_price < resistance
        }

    def calculate_fibonacci_levels(self, data: pd.DataFrame, trend_window: int = 50) -> Dict[str, Any]:
        """
        Calculate Fibonacci retracement levels based on recent trend.

        Args:
            data: OHLCV DataFrame
            trend_window: Window to determine high/low points

        Returns:
            Dictionary with Fibonacci levels
        """
        df = self.prepare_data(data)

        if len(df) < trend_window:
            return {'error': 'Insufficient data for Fibonacci analysis'}

        # Get recent high and low
        recent_data = df.tail(trend_window)
        high_price = recent_data['high'].max()
        low_price = recent_data['low'].min()
        current_price = df['close'].iloc[-1]

        # Calculate Fibonacci levels
        diff = high_price - low_price
        fib_levels = {
            '0.0%': high_price,
            '23.6%': high_price - (diff * 0.236),
            '38.2%': high_price - (diff * 0.382),
            '50.0%': high_price - (diff * 0.500),
            '61.8%': high_price - (diff * 0.618),
            '78.6%': high_price - (diff * 0.786),
            '100.0%': low_price
        }

        # Determine which levels are nearby (within 2% of current price)
        nearby_levels = {}
        for level_name, level_price in fib_levels.items():
            distance_pct = abs((current_price - level_price) / current_price) * 100
            if distance_pct <= 2.0:
                nearby_levels[level_name] = {
                    'price': round(level_price, 2),
                    'distance_pct': round(distance_pct, 2)
                }

        return {
            'fibonacci_levels': {k: round(v, 2) for k, v in fib_levels.items()},
            'nearby_levels': nearby_levels,
            'trend_high': round(high_price, 2),
            'trend_low': round(low_price, 2),
            'current_price': round(current_price, 2)
        }

    def generate_technical_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive technical analysis summary.

        Args:
            data: OHLCV DataFrame

        Returns:
            Complete technical analysis summary
        """
        try:
            # Get all analysis components
            patterns = self.detect_candlestick_patterns(data)
            support_resistance = self.analyze_support_resistance(data)
            fibonacci = self.calculate_fibonacci_levels(data)

            # Calculate overall signal strength
            total_signals = len(patterns.get('patterns_detected', {}))
            bullish_signals = sum(1 for p in patterns.get('patterns_detected', {}).values()
                                 if p.get('direction') == 'bullish')
            bearish_signals = sum(1 for p in patterns.get('patterns_detected', {}).values()
                                 if p.get('direction') == 'bearish')

            # Generate overall sentiment
            if bullish_signals > bearish_signals:
                overall_sentiment = 'bullish'
                confidence = min(90, (bullish_signals / max(total_signals, 1)) * 100)
            elif bearish_signals > bullish_signals:
                overall_sentiment = 'bearish'
                confidence = min(90, (bearish_signals / max(total_signals, 1)) * 100)
            else:
                overall_sentiment = 'neutral'
                confidence = 50

            return {
                'overall_sentiment': overall_sentiment,
                'confidence_score': round(confidence, 1),
                'candlestick_patterns': patterns,
                'support_resistance': support_resistance,
                'fibonacci_analysis': fibonacci,
                'signal_counts': {
                    'total': total_signals,
                    'bullish': bullish_signals,
                    'bearish': bearish_signals
                },
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': f'Technical analysis failed: {str(e)}',
                'analysis_timestamp': datetime.now().isoformat()
            }

    def get_trading_signals(self, technical_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert technical analysis into actionable trading signals.

        Args:
            technical_summary: Output from generate_technical_summary()

        Returns:
            Trading signals and recommendations
        """
        if 'error' in technical_summary:
            return technical_summary

        signals = []

        # Process candlestick patterns
        patterns = technical_summary.get('candlestick_patterns', {}).get('patterns_detected', {})
        for pattern_name, pattern_data in patterns.items():
            if pattern_data['reliability'] >= 75:  # High reliability patterns only
                signal_type = 'BUY' if pattern_data['direction'] == 'bullish' else 'SELL'
                signals.append({
                    'type': signal_type,
                    'source': 'candlestick_pattern',
                    'pattern': pattern_name,
                    'strength': pattern_data['reliability'],
                    'days_ago': pattern_data['days_ago']
                })

        # Process support/resistance signals
        sr_data = technical_summary.get('support_resistance', {})
        if 'error' not in sr_data:
            # Near support = potential buy
            if sr_data.get('support_distance_pct', 100) <= 2:
                signals.append({
                    'type': 'BUY',
                    'source': 'support_level',
                    'level': sr_data['support_level'],
                    'strength': 70
                })

            # Near resistance = potential sell
            if sr_data.get('resistance_distance_pct', 100) <= 2:
                signals.append({
                    'type': 'SELL',
                    'source': 'resistance_level',
                    'level': sr_data['resistance_level'],
                    'strength': 70
                })

        # Process Fibonacci signals
        fib_data = technical_summary.get('fibonacci_analysis', {})
        if 'error' not in fib_data:
            nearby_levels = fib_data.get('nearby_levels', {})
            for level_name, level_data in nearby_levels.items():
                if level_name in ['38.2%', '50.0%', '61.8%']:  # Key retracement levels
                    signals.append({
                        'type': 'WATCH',
                        'source': 'fibonacci_level',
                        'level': level_name,
                        'price': level_data['price'],
                        'strength': 60
                    })

        # Aggregate signals into recommendation
        buy_signals = [s for s in signals if s['type'] == 'BUY']
        sell_signals = [s for s in signals if s['type'] == 'SELL']

        if len(buy_signals) > len(sell_signals):
            recommendation = 'BUY'
            confidence = min(85, sum(s['strength'] for s in buy_signals) / len(buy_signals))
        elif len(sell_signals) > len(buy_signals):
            recommendation = 'SELL'
            confidence = min(85, sum(s['strength'] for s in sell_signals) / len(sell_signals))
        else:
            recommendation = 'HOLD'
            confidence = 50

        return {
            'recommendation': recommendation,
            'confidence': round(confidence, 1),
            'signals': signals,
            'signal_summary': {
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'total_signals': len(signals)
            }
        }


def analyze_stock_patterns(ticker: str, data: pd.DataFrame, config: Dict[str, Any] = None) -> str:
    """
    Main function to analyze stock patterns and return formatted report.

    Args:
        ticker: Stock ticker symbol
        data: OHLCV DataFrame
        config: Optional configuration parameters

    Returns:
        Formatted technical analysis report
    """
    analyzer = TechnicalPatternAnalyzer(config)

    try:
        # Generate technical summary
        technical_summary = analyzer.generate_technical_summary(data)

        if 'error' in technical_summary:
            return f"Technical Analysis Error for {ticker}: {technical_summary['error']}"

        # Get trading signals
        trading_signals = analyzer.get_trading_signals(technical_summary)

        # Format report
        report = f"""# Technical Analysis Report: {ticker}

## Overall Assessment
- **Technical Sentiment:** {technical_summary['overall_sentiment'].upper()}
- **Confidence Score:** {technical_summary['confidence_score']}%
- **Recommendation:** {trading_signals['recommendation']} (Confidence: {trading_signals['confidence']}%)

## Candlestick Pattern Analysis
"""

        patterns = technical_summary['candlestick_patterns']['patterns_detected']
        if patterns:
            for pattern_name, pattern_data in patterns.items():
                report += f"- **{pattern_name}** ({pattern_data['direction']}): Reliability {pattern_data['reliability']}%, detected {pattern_data['days_ago']} days ago\n"
        else:
            report += "- No significant candlestick patterns detected in recent trading\n"

        # Support/Resistance section
        sr_data = technical_summary['support_resistance']
        if 'error' not in sr_data:
            report += f"""
## Support & Resistance Analysis
- **Current Price:** ${sr_data['current_price']}
- **Support Level:** ${sr_data['support_level']} ({sr_data['support_distance_pct']}% below current)
- **Resistance Level:** ${sr_data['resistance_level']} ({sr_data['resistance_distance_pct']}% above current)
- **Price Range Status:** {'Within range' if sr_data['in_range'] else 'Outside range'}
"""

        # Fibonacci section
        fib_data = technical_summary['fibonacci_analysis']
        if 'error' not in fib_data and fib_data['nearby_levels']:
            report += "\n## Fibonacci Analysis\n"
            report += f"**Key Levels Near Current Price:**\n"
            for level_name, level_data in fib_data['nearby_levels'].items():
                report += f"- {level_name}: ${level_data['price']} ({level_data['distance_pct']}% away)\n"

        # Trading signals section
        if trading_signals['signals']:
            report += "\n## Trading Signals\n"
            for signal in trading_signals['signals']:
                report += f"- **{signal['type']}** signal from {signal['source']} (Strength: {signal['strength']}%)\n"

        # Summary table
        report += f"""
## Signal Summary

| Metric | Value |
|--------|-------|
| Overall Sentiment | {technical_summary['overall_sentiment'].upper()} |
| Confidence Score | {technical_summary['confidence_score']}% |
| Recommendation | {trading_signals['recommendation']} |
| Patterns Detected | {technical_summary['signal_counts']['total']} |
| Bullish Signals | {technical_summary['signal_counts']['bullish']} |
| Bearish Signals | {technical_summary['signal_counts']['bearish']} |
| Support Distance | {sr_data.get('support_distance_pct', 'N/A')}% |
| Resistance Distance | {sr_data.get('resistance_distance_pct', 'N/A')}% |

*Analysis generated on {technical_summary['analysis_timestamp'][:19]}*
"""

        return report

    except Exception as e:
        return f"Technical Analysis Error for {ticker}: {str(e)}"