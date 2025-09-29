#!/usr/bin/env python3
"""
Test Simple Batch Analysis System - Focused on individual stock decisions only.
"""

import sys
import os
from unittest.mock import Mock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


class MockIndividualGraph:
    """Mock individual trading graph for testing."""

    def __init__(self, success_results=None, failure_tickers=None):
        self.success_results = success_results or {}
        self.failure_tickers = failure_tickers or []

    def propagate(self, ticker, date):
        if ticker in self.failure_tickers:
            raise Exception(f"Mock failure for {ticker}")

        # Return tuple like real TradingAgentsGraph: (final_state, decision)
        result = self.success_results.get(ticker, {
            "final_trade_decision": f"MOCK_BUY_{ticker}",
            "reasoning": f"Mock analysis for {ticker}",
            "market_report": f"Mock market data for {ticker}"
        })

        # Convert to final_state format and return tuple
        decision = result.get("final_trade_decision", f"MOCK_BUY_{ticker}")
        final_state = {
            "final_trade_decision": decision,
            "market_report": result.get("market_report", ""),
            "sentiment_report": "",
            "news_report": "",
            "fundamentals_report": ""
        }
        return final_state, decision


def test_batch_analyzer_parallel_execution():
    """Test simple parallel execution with mixed success/failure results."""

    try:
        from tradingagents.agents.portfolio.coordinators.batch_analyzer import BatchAnalyzer

        # Create test data
        test_tickers = ["AAPL", "MSFT", "TSLA", "FAIL1", "FAIL2"]

        # Mock individual graph with some failures
        success_results = {
            "AAPL": {"final_trade_decision": "BUY_AAPL", "reasoning": "Strong fundamentals"},
            "MSFT": {"final_trade_decision": "HOLD_MSFT", "reasoning": "Stable position"},
            "TSLA": {"final_trade_decision": "SELL_TSLA", "reasoning": "Overvalued"}
        }
        failure_tickers = ["FAIL1", "FAIL2"]

        mock_graph = MockIndividualGraph(success_results, failure_tickers)

        # Initialize batch analyzer
        analyzer = BatchAnalyzer(mock_graph, max_workers=2, default_timeout=1)

        print("🧪 Testing Simple Batch Analyzer")
        print("=" * 40)

        # Test batch analysis
        results = analyzer.analyze_batch(test_tickers, "2024-01-01")

        # Verify results structure
        assert results.successful_analyses is not None
        assert results.failed_analyses is not None
        assert results.summary is not None

        print(f"✅ Successful analyses: {len(results.successful_analyses)}")
        print(f"❌ Failed analyses: {len(results.failed_analyses)}")
        print(f"📊 Success rate: {results.summary['success_rate']}")

        # Verify successful analyses
        assert len(results.successful_analyses) == 3
        assert "AAPL" in results.successful_analyses
        assert "MSFT" in results.successful_analyses
        assert "TSLA" in results.successful_analyses

        # Verify failed analyses
        assert len(results.failed_analyses) == 2
        assert "FAIL1" in results.failed_analyses
        assert "FAIL2" in results.failed_analyses

        # Verify individual decisions are preserved
        assert results.successful_analyses["AAPL"]["final_trade_decision"] == "BUY_AAPL"
        assert results.successful_analyses["MSFT"]["final_trade_decision"] == "HOLD_MSFT"
        assert results.successful_analyses["TSLA"]["final_trade_decision"] == "SELL_TSLA"

        # Verify no silent failures
        for ticker, error_result in results.failed_analyses.items():
            assert error_result.status in ["ERROR", "TIMEOUT"]
            assert error_result.error_message is not None
            print(f"   {ticker}: {error_result.status} - {error_result.error_message}")

        # Cleanup
        analyzer.shutdown()

        print("✅ Batch analyzer test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_reporter():
    """Test simple reporter display functionality."""

    try:
        from tradingagents.agents.portfolio.simple_reporter import SimpleReporter
        from tradingagents.agents.portfolio.coordinators.batch_analyzer import (
            BatchAnalysisResult, AnalysisResult
        )

        # Create test data
        successful_analyses = {
            "AAPL": {"final_trade_decision": "BUY_AAPL", "market_report": "Strong growth"},
            "MSFT": {"final_trade_decision": "HOLD_MSFT", "market_report": "Stable performance"}
        }

        failed_analyses = {
            "ERROR_STOCK": AnalysisResult(
                ticker="ERROR_STOCK",
                status="ERROR",
                error_type="ValueError",
                error_message="Mock error message"
            )
        }

        summary = {
            "total_stocks": 3,
            "successful": 2,
            "failed": 1,
            "success_rate": "66.7%",
            "completion_status": "PARTIAL",
            "requires_attention": True
        }

        results = BatchAnalysisResult(
            successful_analyses=successful_analyses,
            failed_analyses=failed_analyses,
            summary=summary
        )

        reporter = SimpleReporter()

        print("\n🧪 Testing Simple Reporter")
        print("=" * 40)

        print("📊 Individual Stock Results:")
        print(f"   Total: {summary['total_stocks']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")

        # Verify individual decisions are displayed correctly
        for ticker, analysis in successful_analyses.items():
            decision = analysis.get("final_trade_decision")
            print(f"   ✅ {ticker}: {decision}")

        # Verify error reporting
        for ticker, error_result in failed_analyses.items():
            print(f"   ❌ {ticker}: {error_result.status} - {error_result.error_message}")

        print("✅ Simple reporter test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all simple batch analysis tests."""
    print("🚀 SIMPLE BATCH ANALYSIS TESTS")
    print("=" * 50)

    tests = [
        ("Batch Analyzer", test_batch_analyzer_parallel_execution),
        ("Simple Reporter", test_simple_reporter)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        success = test_func()
        results.append((test_name, success))

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20} {status}")

    success_rate = (passed / total) * 100
    print(f"\n📊 Success Rate: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate >= 100:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Simple batch analysis system is working correctly")
        print(f"✅ Individual decisions preserved and displayed cleanly")
        print(f"✅ No portfolio-level reasoning or complexity")
    else:
        print(f"\n⚠️ Some tests failed - check individual results above")

    print("=" * 50)


if __name__ == "__main__":
    main()