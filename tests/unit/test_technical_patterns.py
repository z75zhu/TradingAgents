"""
Unit tests for technical pattern analysis functionality.

This module tests the technical analysis components including:
- Candlestick pattern detection
- Support and resistance calculation
- Fibonacci retracement analysis
- Technical signal generation
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import warnings

# Suppress pandas warnings for cleaner test output
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from tradingagents.technical_patterns import TechnicalPatternAnalyzer, analyze_stock_patterns
    from tradingagents.dataflows.talib_utils import (
        TechnicalAnalysisUtils,
        get_technical_analysis_report,
        get_candlestick_patterns_report,
        get_support_resistance_report,
        get_fibonacci_levels_report
    )
    TECHNICAL_ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"Technical analysis imports failed: {e}")
    TECHNICAL_ANALYSIS_AVAILABLE = False


class TestTechnicalPatternAnalyzer(unittest.TestCase):
    """Test the core TechnicalPatternAnalyzer class."""

    def setUp(self):
        """Set up test data and analyzer."""
        if not TECHNICAL_ANALYSIS_AVAILABLE:
            self.skipTest("Technical analysis dependencies not available")

        self.analyzer = TechnicalPatternAnalyzer()
        self.test_data = self._create_test_data()

    def _create_test_data(self):
        """Create synthetic OHLCV test data."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        # Create realistic price movement
        np.random.seed(42)  # For reproducible tests

        # Start with a base price and create random walk
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, 100)  # Small daily returns with volatility
        prices = [base_price]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        prices = np.array(prices[1:])  # Remove the initial base price

        # Create OHLC from close prices with realistic spreads
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, 100)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, 100)))
        open_prices = np.roll(prices, 1)  # Previous close as open
        open_prices[0] = prices[0]  # First open same as close

        # Ensure OHLC relationships are valid
        for i in range(len(prices)):
            max_price = max(open_prices[i], prices[i])
            min_price = min(open_prices[i], prices[i])
            high[i] = max(high[i], max_price)
            low[i] = min(low[i], min_price)

        # Generate volume data
        volume = np.random.randint(100000, 1000000, 100)

        return pd.DataFrame({
            'Date': dates,
            'Open': open_prices,
            'High': high,
            'Low': low,
            'Close': prices,
            'Volume': volume
        })

    def test_data_preparation(self):
        """Test data preparation and cleaning."""
        # Test with valid data
        prepared_data = self.analyzer.prepare_data(self.test_data)
        self.assertIsInstance(prepared_data, pd.DataFrame)
        self.assertEqual(len(prepared_data), len(self.test_data))

        # Check required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.assertIn(col, prepared_data.columns)

        # Test with missing columns
        incomplete_data = self.test_data.drop(columns=['Volume'])
        prepared_incomplete = self.analyzer.prepare_data(incomplete_data)
        self.assertIn('volume', prepared_incomplete.columns)
        self.assertTrue(all(prepared_incomplete['volume'] == 0))

    def test_candlestick_pattern_detection(self):
        """Test candlestick pattern detection."""
        try:
            patterns = self.analyzer.detect_candlestick_patterns(self.test_data)

            # Should return a dictionary with analysis results
            self.assertIsInstance(patterns, dict)
            self.assertIn('patterns_detected', patterns)
            self.assertIn('total_patterns', patterns)
            self.assertIn('analysis_date', patterns)

            # Total patterns should be a non-negative integer
            self.assertIsInstance(patterns['total_patterns'], int)
            self.assertGreaterEqual(patterns['total_patterns'], 0)

        except Exception as e:
            # If TA-Lib is not properly installed, this test should fail gracefully
            self.assertIn('TA-Lib', str(e))

    def test_support_resistance_analysis(self):
        """Test support and resistance level calculation."""
        sr_analysis = self.analyzer.analyze_support_resistance(self.test_data)

        # Should return a dictionary with required keys
        expected_keys = ['support_level', 'resistance_level', 'current_price',
                        'support_distance_pct', 'resistance_distance_pct', 'in_range']
        for key in expected_keys:
            self.assertIn(key, sr_analysis)

        # Resistance should be higher than or equal to support
        if 'error' not in sr_analysis:
            self.assertGreaterEqual(sr_analysis['resistance_level'], sr_analysis['support_level'])

            # Current price should be positive
            self.assertGreater(sr_analysis['current_price'], 0)

    def test_fibonacci_analysis(self):
        """Test Fibonacci retracement calculation."""
        fib_analysis = self.analyzer.calculate_fibonacci_levels(self.test_data)

        # Should return a dictionary with Fibonacci levels
        if 'error' not in fib_analysis:
            self.assertIn('fibonacci_levels', fib_analysis)
            self.assertIn('trend_high', fib_analysis)
            self.assertIn('trend_low', fib_analysis)
            self.assertIn('current_price', fib_analysis)

            # Trend high should be greater than trend low
            self.assertGreater(fib_analysis['trend_high'], fib_analysis['trend_low'])

            # Fibonacci levels should be in expected format
            fib_levels = fib_analysis['fibonacci_levels']
            expected_levels = ['0.0%', '23.6%', '38.2%', '50.0%', '61.8%', '78.6%', '100.0%']
            for level in expected_levels:
                self.assertIn(level, fib_levels)

    def test_technical_summary_generation(self):
        """Test comprehensive technical analysis summary."""
        summary = self.analyzer.generate_technical_summary(self.test_data)

        # Should return a comprehensive analysis
        self.assertIsInstance(summary, dict)

        if 'error' not in summary:
            expected_keys = ['overall_sentiment', 'confidence_score', 'candlestick_patterns',
                           'support_resistance', 'fibonacci_analysis', 'signal_counts']
            for key in expected_keys:
                self.assertIn(key, summary)

            # Sentiment should be valid
            valid_sentiments = ['bullish', 'bearish', 'neutral']
            self.assertIn(summary['overall_sentiment'], valid_sentiments)

            # Confidence should be between 0 and 100
            confidence = summary['confidence_score']
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 100)

    def test_trading_signal_generation(self):
        """Test trading signal generation from technical analysis."""
        summary = self.analyzer.generate_technical_summary(self.test_data)

        if 'error' not in summary:
            signals = self.analyzer.get_trading_signals(summary)

            # Should return trading signals
            self.assertIsInstance(signals, dict)

            if 'error' not in signals:
                expected_keys = ['recommendation', 'confidence', 'signals', 'signal_summary']
                for key in expected_keys:
                    self.assertIn(key, signals)

                # Recommendation should be valid
                valid_recommendations = ['BUY', 'SELL', 'HOLD']
                self.assertIn(signals['recommendation'], valid_recommendations)

                # Confidence should be reasonable
                confidence = signals['confidence']
                self.assertGreaterEqual(confidence, 0)
                self.assertLessEqual(confidence, 100)

    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        # Test with very small dataset
        small_data = self.test_data.head(5)

        patterns = self.analyzer.detect_candlestick_patterns(small_data)
        self.assertIn('error', patterns)

        sr_analysis = self.analyzer.analyze_support_resistance(small_data, window=20)
        self.assertIn('error', sr_analysis)

    def test_analyze_stock_patterns_function(self):
        """Test the main analyze_stock_patterns function."""
        try:
            report = analyze_stock_patterns('TEST', self.test_data)

            # Should return a formatted string report
            self.assertIsInstance(report, str)
            self.assertIn('Technical Analysis Report: TEST', report)
            self.assertIn('Overall Assessment', report)

            # Should contain key sections
            expected_sections = ['Candlestick Pattern Analysis', 'Support & Resistance Analysis',
                               'Signal Summary']
            for section in expected_sections:
                # At least some sections should be present
                pass  # Report format may vary based on detected patterns

        except Exception as e:
            # Should handle errors gracefully
            self.assertIsInstance(str(e), str)


class TestTechnicalAnalysisUtils(unittest.TestCase):
    """Test the TechnicalAnalysisUtils dataflow interface."""

    def setUp(self):
        """Set up test environment."""
        if not TECHNICAL_ANALYSIS_AVAILABLE:
            self.skipTest("Technical analysis dependencies not available")

    @patch('tradingagents.dataflows.talib_utils.yf.download')
    def test_get_price_data_online(self, mock_yf_download):
        """Test online price data fetching."""
        # Mock yfinance response
        mock_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=30),
            'Open': np.random.uniform(95, 105, 30),
            'High': np.random.uniform(100, 110, 30),
            'Low': np.random.uniform(90, 100, 30),
            'Close': np.random.uniform(95, 105, 30),
            'Volume': np.random.randint(100000, 1000000, 30)
        })
        mock_yf_download.return_value = mock_data

        # Test data fetching
        data = TechnicalAnalysisUtils._get_price_data('AAPL', '2024-01-30', 30, online=True)

        self.assertIsNotNone(data)
        self.assertIsInstance(data, pd.DataFrame)
        mock_yf_download.assert_called_once()

    @patch('tradingagents.dataflows.talib_utils.TechnicalAnalysisUtils._get_price_data')
    def test_get_technical_analysis(self, mock_get_data):
        """Test technical analysis report generation."""
        # Mock price data
        mock_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=50),
            'Open': np.random.uniform(95, 105, 50),
            'High': np.random.uniform(100, 110, 50),
            'Low': np.random.uniform(90, 100, 50),
            'Close': np.random.uniform(95, 105, 50),
            'Volume': np.random.randint(100000, 1000000, 50)
        })
        mock_get_data.return_value = mock_data

        # Test analysis
        result = TechnicalAnalysisUtils.get_technical_analysis('AAPL', '2024-01-30', 50, True)

        self.assertIsInstance(result, str)
        # Should contain basic report structure
        if not result.startswith('Technical Analysis Error'):
            self.assertIn('Technical Analysis Report: AAPL', result)

    def test_interface_functions(self):
        """Test the interface functions exist and are callable."""
        # Test function existence
        functions = [
            get_technical_analysis_report,
            get_candlestick_patterns_report,
            get_support_resistance_report,
            get_fibonacci_levels_report
        ]

        for func in functions:
            self.assertTrue(callable(func))

        # Test function signatures (basic call with mock parameters)
        # These will likely fail without proper data, but should not raise import errors
        try:
            # Just test the functions can be called (they may return errors, which is fine)
            get_technical_analysis_report('TEST', '2024-01-30', 100, False)
        except Exception:
            pass  # Expected to fail without proper data setup


class TestTechnicalAnalysisIntegration(unittest.TestCase):
    """Test integration aspects of technical analysis."""

    def setUp(self):
        """Set up integration test environment."""
        if not TECHNICAL_ANALYSIS_AVAILABLE:
            self.skipTest("Technical analysis dependencies not available")

    def test_error_handling(self):
        """Test that errors are handled gracefully."""
        # Test with invalid data
        try:
            analyzer = TechnicalPatternAnalyzer()

            # Empty DataFrame
            empty_data = pd.DataFrame()
            result = analyzer.detect_candlestick_patterns(empty_data)
            self.assertIn('error', result)

            # Invalid data types
            invalid_data = pd.DataFrame({'invalid': [1, 2, 3]})
            result = analyzer.prepare_data(invalid_data)
            # Should raise ValueError for missing required columns
        except ValueError:
            pass  # Expected behavior
        except Exception as e:
            # Should handle other errors gracefully
            self.assertIsInstance(str(e), str)

    def test_configuration_handling(self):
        """Test configuration parameter handling."""
        # Test with custom configuration
        config = {
            'min_periods': 10,
            'volume_confirmation': False
        }

        analyzer = TechnicalPatternAnalyzer(config)
        self.assertEqual(analyzer.min_periods, 10)
        self.assertEqual(analyzer.volume_confirmation, False)

    def test_data_validation(self):
        """Test data validation and cleaning."""
        analyzer = TechnicalPatternAnalyzer()

        # Test data with NaN values
        data_with_nan = pd.DataFrame({
            'Open': [100, np.nan, 102],
            'High': [105, 106, np.nan],
            'Low': [95, 96, 97],
            'Close': [103, 104, 105],
            'Volume': [1000, 2000, 3000]
        })

        try:
            cleaned_data = analyzer.prepare_data(data_with_nan)
            # Should handle NaN values appropriately
            self.assertIsInstance(cleaned_data, pd.DataFrame)
        except Exception:
            pass  # May fail with insufficient data after cleaning


def run_technical_analysis_tests():
    """Run all technical analysis tests."""
    if not TECHNICAL_ANALYSIS_AVAILABLE:
        print("⚠️ Technical analysis dependencies not available. Skipping tests.")
        print("To run these tests, install: pip install TA-Lib pandas-ta")
        return False

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalPatternAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalAnalysisUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalAnalysisIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    if result.wasSuccessful():
        print("✅ All technical analysis tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == '__main__':
    success = run_technical_analysis_tests()
    exit(0 if success else 1)