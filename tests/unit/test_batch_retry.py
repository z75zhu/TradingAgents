#!/usr/bin/env python3
"""
Test suite for batch analysis retry mechanism.

Tests the retry logic for handling throttling errors without actually
invoking the expensive TradingAgents analysis.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from dataclasses import dataclass
from typing import Dict, Any

# Import the retry classes and functions
from tradingagents.agents.portfolio_batch import (
    RetryableTask,
    BatchAnalysisState,
    classify_error,
    analyze_ticker_safe,
    run_batch_analysis_with_retry
)


class TestRetryableTask(unittest.TestCase):
    """Test RetryableTask functionality."""

    def test_should_retry_throttling_error(self):
        """Test that throttling errors are marked as retryable."""
        task = RetryableTask("AAPL", "2025-01-26")
        task.increment_attempt("ThrottlingException: Too many tokens")

        # Should retry for throttling errors with attempts < 3
        self.assertTrue(task.should_retry())

        # After 3 attempts, should not retry
        task.attempt = 3
        self.assertFalse(task.should_retry())

    def test_should_not_retry_non_throttling_error(self):
        """Test that non-throttling errors are not retryable."""
        task = RetryableTask("AAPL", "2025-01-26")
        task.increment_attempt("Invalid ticker symbol")
        task.last_error = "Invalid ticker symbol"

        # Should not retry for non-throttling errors
        self.assertFalse(task.should_retry())

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff timing."""
        task = RetryableTask("AAPL", "2025-01-26")

        # First attempt: base delay ~30s
        task.increment_attempt("ThrottlingException")
        first_delay = task.next_retry_time - time.time()
        self.assertGreater(first_delay, 15)  # At least minimum delay
        self.assertLess(first_delay, 50)     # Not too much with jitter

        # Second attempt: base delay ~60s
        task.increment_attempt("ThrottlingException")
        second_delay = task.next_retry_time - time.time()
        self.assertGreater(second_delay, 40)
        self.assertLess(second_delay, 90)


class TestBatchAnalysisState(unittest.TestCase):
    """Test BatchAnalysisState functionality."""

    def test_completion_tracking(self):
        """Test completion rate calculation."""
        state = BatchAnalysisState()
        state.total_tickers = 5

        # Initially 0% complete
        self.assertEqual(state.completion_rate, 0.0)

        # Add some successes
        state.add_success("AAPL", {"decision": "BUY"})
        state.add_success("MSFT", {"decision": "HOLD"})
        self.assertEqual(state.completion_rate, 0.4)  # 2/5

        # Add failure
        state.add_permanent_failure("TSLA", "Error")
        self.assertEqual(state.completion_rate, 0.6)  # 3/5

        # Complete all
        state.add_success("GOOGL", {"decision": "SELL"})
        state.add_success("AMZN", {"decision": "BUY"})
        self.assertEqual(state.completion_rate, 1.0)  # 5/5
        self.assertTrue(state.is_complete)

    def test_retry_queue_management(self):
        """Test retry queue operations."""
        state = BatchAnalysisState()

        # Add retry tasks
        task1 = RetryableTask("AAPL", "2025-01-26")
        task1.next_retry_time = time.time() - 10  # Ready now

        task2 = RetryableTask("MSFT", "2025-01-26")
        task2.next_retry_time = time.time() + 60   # Not ready yet

        state.add_retry(task1)
        state.add_retry(task2)

        # Only task1 should be ready
        ready_tasks = state.get_ready_retries()
        self.assertEqual(len(ready_tasks), 1)
        self.assertEqual(ready_tasks[0].ticker, "AAPL")

        # task2 should still be in queue
        self.assertEqual(len(state.retry_queue), 1)
        self.assertEqual(state.retry_queue[0].ticker, "MSFT")


class TestErrorClassification(unittest.TestCase):
    """Test error classification logic."""

    def test_throttling_error_classification(self):
        """Test throttling error detection."""
        errors = [
            "ThrottlingException: Too many tokens",
            "botocore.errorfactory.ThrottlingException",
            "too many tokens, please wait"
        ]

        for error in errors:
            self.assertEqual(classify_error(error), "throttling")

    def test_other_error_classifications(self):
        """Test other error type classifications."""
        test_cases = [
            ("Connection timeout", "network"),
            ("Invalid ticker symbol", "data"),
            ("Permission denied", "auth"),
            ("Random unknown error", "unknown")
        ]

        for error_msg, expected_type in test_cases:
            self.assertEqual(classify_error(error_msg), expected_type)


class TestMockedBatchAnalysis(unittest.TestCase):
    """Test batch analysis with mocked TradingAgents calls."""

    def test_successful_analysis_no_retries(self):
        """Test batch analysis with all successful results."""
        # Mock successful TradingAgents calls
        mock_graph = Mock()
        mock_graph.propagate.return_value = (
            {"final_trade_decision": "Analysis complete"},
            "BUY"
        )

        tickers = ["AAPL", "MSFT", "GOOGL"]
        results = run_batch_analysis_with_retry(
            mock_graph, tickers, "2025-01-26", max_workers=2, max_total_time=60
        )

        # Should have 3 successful analyses, 0 failed
        self.assertEqual(len(results["successful"]), 3)
        self.assertEqual(len(results["failed"]), 0)
        self.assertEqual(results["retry_stats"]["total_rounds"], 1)

    def test_throttling_with_retry_success(self):
        """Test throttling errors that succeed on retry."""
        mock_graph = Mock()

        # First calls fail with throttling, second calls succeed
        call_count = 0
        def mock_propagate(ticker, date):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First two calls fail
                raise Exception("ThrottlingException: Too many tokens")
            else:  # Subsequent calls succeed
                return {"final_trade_decision": "Analysis complete"}, "BUY"

        mock_graph.propagate.side_effect = mock_propagate

        # Mock both time.sleep and time.time for faster testing
        with patch('time.sleep') as mock_sleep, \
             patch('tradingagents.agents.portfolio_batch.time.time') as mock_time:

            # Mock time progression to simulate immediate retry readiness
            mock_time.side_effect = [1000, 1001, 1002, 1003, 1004, 1005]  # Always increasing

            results = run_batch_analysis_with_retry(
                mock_graph, ["AAPL", "MSFT"], "2025-01-26",
                max_workers=1, max_total_time=120
            )

        # Should eventually succeed for both tickers
        self.assertEqual(len(results["successful"]), 2)
        self.assertEqual(len(results["failed"]), 0)
        self.assertGreater(results["retry_stats"]["total_rounds"], 1)

    def test_permanent_failure_no_retry(self):
        """Test that non-retryable errors fail permanently."""
        mock_graph = Mock()
        mock_graph.propagate.side_effect = Exception("Invalid ticker symbol")

        results = run_batch_analysis_with_retry(
            mock_graph, ["INVALID"], "2025-01-26", max_workers=1, max_total_time=60
        )

        # Should fail permanently without retry
        self.assertEqual(len(results["successful"]), 0)
        self.assertEqual(len(results["failed"]), 1)
        self.assertEqual(results["retry_stats"]["total_rounds"], 1)
        self.assertIn("Invalid ticker symbol", results["failed"]["INVALID"]["error"])


if __name__ == "__main__":
    # Set up logging to see test output
    import logging
    logging.basicConfig(level=logging.INFO)

    # Run specific test groups
    print("🧪 Testing RetryableTask...")
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestRetryableTask)
    )

    print("\n🧪 Testing BatchAnalysisState...")
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestBatchAnalysisState)
    )

    print("\n🧪 Testing Error Classification...")
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestErrorClassification)
    )

    print("\n🧪 Testing Mocked Batch Analysis...")
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(TestMockedBatchAnalysis)
    )

    print("\n✅ All retry mechanism tests completed!")