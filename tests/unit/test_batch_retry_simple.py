#!/usr/bin/env python3
"""
Simplified test suite for batch analysis retry mechanism.
Tests core retry logic without complex time mocking.
"""

import unittest
from unittest.mock import Mock
import time

# Import the retry classes and functions
from tradingagents.agents.portfolio_batch import (
    RetryableTask,
    BatchAnalysisState,
    classify_error,
    analyze_ticker_safe
)


class TestRetryMechanismSimple(unittest.TestCase):
    """Test core retry mechanism functionality."""

    def test_error_classification(self):
        """Test that errors are classified correctly for retry decisions."""
        # Throttling errors should be retryable
        self.assertEqual(classify_error("ThrottlingException: Too many tokens"), "throttling")
        self.assertEqual(classify_error("too many tokens, please wait"), "throttling")

        # Other errors should not be retryable
        self.assertEqual(classify_error("Invalid ticker symbol"), "data")
        self.assertEqual(classify_error("Connection timeout"), "network")
        self.assertEqual(classify_error("Permission denied"), "auth")

    def test_retryable_task_logic(self):
        """Test RetryableTask retry decision logic."""
        task = RetryableTask("AAPL", "2025-01-26")

        # Initially should not retry (no error)
        self.assertFalse(task.should_retry())

        # After throttling error, should retry (attempt < 3)
        task.increment_attempt("ThrottlingException: Too many tokens")
        self.assertTrue(task.should_retry())
        self.assertEqual(task.attempt, 1)

        # After 3 attempts, should not retry
        task.attempt = 3
        self.assertFalse(task.should_retry())

    def test_batch_state_tracking(self):
        """Test BatchAnalysisState completion tracking."""
        state = BatchAnalysisState()
        state.total_tickers = 3

        # Initially incomplete
        self.assertFalse(state.is_complete)
        self.assertEqual(state.completion_rate, 0.0)

        # Add success
        state.add_success("AAPL", {"decision": "BUY", "status": "success"})
        self.assertEqual(state.completion_rate, 1/3)

        # Add failure
        state.add_permanent_failure("TSLA", "Invalid ticker")
        self.assertEqual(state.completion_rate, 2/3)

        # Add final success
        state.add_success("MSFT", {"decision": "HOLD", "status": "success"})
        self.assertEqual(state.completion_rate, 1.0)
        self.assertTrue(state.is_complete)

    def test_analyze_ticker_safe_success(self):
        """Test successful ticker analysis."""
        mock_graph = Mock()
        mock_graph.propagate.return_value = (
            {"final_trade_decision": "Analysis complete"},
            "BUY"
        )

        result = analyze_ticker_safe(mock_graph, "AAPL", "2025-01-26")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["decision"], "BUY")

    def test_analyze_ticker_safe_throttling_error(self):
        """Test ticker analysis with throttling error."""
        mock_graph = Mock()
        mock_graph.propagate.side_effect = Exception("ThrottlingException: Too many tokens")

        result = analyze_ticker_safe(mock_graph, "AAPL", "2025-01-26")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["error_type"], "throttling")
        self.assertTrue(result["retryable"])

    def test_analyze_ticker_safe_permanent_error(self):
        """Test ticker analysis with permanent error."""
        mock_graph = Mock()
        mock_graph.propagate.side_effect = Exception("Invalid ticker symbol")

        result = analyze_ticker_safe(mock_graph, "INVALID", "2025-01-26")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["ticker"], "INVALID")
        self.assertEqual(result["error_type"], "data")
        self.assertFalse(result["retryable"])

    def test_retry_queue_operations(self):
        """Test retry queue management."""
        state = BatchAnalysisState()

        # Create tasks with different retry times
        task1 = RetryableTask("AAPL", "2025-01-26")
        task1.next_retry_time = time.time() - 10  # Ready now

        task2 = RetryableTask("MSFT", "2025-01-26")
        task2.next_retry_time = time.time() + 60   # Not ready yet

        state.add_retry(task1)
        state.add_retry(task2)

        # Get ready retries
        ready_tasks = state.get_ready_retries()

        # Only task1 should be ready
        self.assertEqual(len(ready_tasks), 1)
        self.assertEqual(ready_tasks[0].ticker, "AAPL")

        # task2 should still be in queue
        self.assertEqual(len(state.retry_queue), 1)
        self.assertEqual(state.retry_queue[0].ticker, "MSFT")


def run_simple_tests():
    """Run the simplified retry tests."""
    print("🧪 Running simplified retry mechanism tests...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRetryMechanismSimple)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Report results
    if result.wasSuccessful():
        print("✅ All retry mechanism tests passed!")
        return True
    else:
        print("❌ Some retry mechanism tests failed!")
        return False


if __name__ == "__main__":
    success = run_simple_tests()
    exit(0 if success else 1)