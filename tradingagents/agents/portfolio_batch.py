"""
Simple Portfolio Batch Analysis - Minimal implementation for running individual stock analyses.

Focus: Load tickers, run in parallel, show results. No complex error handling or portfolio logic.
"""

import json
import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RetryableTask:
    """Represents a task that can be retried with backoff strategy."""
    ticker: str
    date: str
    attempt: int = 0
    last_error: str = ""
    next_retry_time: float = 0.0

    def should_retry(self) -> bool:
        """Check if task should be retried based on error type and attempt count."""
        # Only retry for throttling errors, up to 3 attempts
        return (self.attempt < 3 and
                "ThrottlingException" in self.last_error)

    def calculate_next_retry(self) -> float:
        """Calculate exponential backoff with jitter."""
        # Base delay: 30s, 60s, 120s with ±25% jitter
        base_delay = 30 * (2 ** self.attempt)
        jitter = base_delay * 0.25 * (2 * random.random() - 1)  # ±25%
        delay = max(15, base_delay + jitter)  # Minimum 15 seconds
        return time.time() + delay

    def increment_attempt(self, error_msg: str):
        """Increment attempt counter and set next retry time."""
        self.attempt += 1
        self.last_error = error_msg
        self.next_retry_time = self.calculate_next_retry()


@dataclass
class BatchAnalysisState:
    """Tracks state of batch analysis with retry capabilities."""
    successful: Dict[str, Any] = field(default_factory=dict)
    failed: Dict[str, Any] = field(default_factory=dict)
    retry_queue: List[RetryableTask] = field(default_factory=list)
    total_tickers: int = 0
    completed_count: int = 0

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate (0.0 to 1.0)."""
        if self.total_tickers == 0:
            return 1.0
        return self.completed_count / self.total_tickers

    @property
    def is_complete(self) -> bool:
        """Check if all analyses are complete (successful or permanently failed)."""
        return len(self.successful) + len(self.failed) >= self.total_tickers

    def add_success(self, ticker: str, result: Dict[str, Any]):
        """Add successful analysis result."""
        self.successful[ticker] = result
        self.completed_count += 1

    def add_retry(self, task: RetryableTask):
        """Add task to retry queue."""
        self.retry_queue.append(task)

    def add_permanent_failure(self, ticker: str, error: str):
        """Add permanently failed analysis."""
        self.failed[ticker] = {"ticker": ticker, "status": "error", "error": error}
        self.completed_count += 1

    def get_ready_retries(self) -> List[RetryableTask]:
        """Get tasks ready for retry based on their next_retry_time."""
        current_time = time.time()
        ready_tasks = [task for task in self.retry_queue if task.next_retry_time <= current_time]

        # Remove ready tasks from queue
        for task in ready_tasks:
            self.retry_queue.remove(task)

        return ready_tasks


def load_portfolio_tickers(portfolio_file: str = "portfolio.json") -> List[str]:
    """Load ticker list from simple portfolio JSON file."""
    try:
        with open(portfolio_file, 'r') as f:
            data = json.load(f)
        return [pos["ticker"] for pos in data.get("positions", [])]
    except Exception as e:
        logger.error(f"Failed to load portfolio from {portfolio_file}: {e}")
        return []


def analyze_ticker_safe(graph, ticker: str, date: str) -> Dict[str, Any]:
    """Safely analyze a single ticker with comprehensive error handling."""
    try:
        logger.info(f"Starting analysis for {ticker}")
        final_state, decision = graph.propagate(ticker, date)
        logger.info(f"Successfully completed analysis for {ticker}: {decision}")
        return {
            "ticker": ticker,
            "status": "success",
            "decision": decision,
            "report": final_state.get("final_trade_decision", "")
        }
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Analysis failed for {ticker}: {error_msg}")

        # Classify error type for retry decision
        error_classification = classify_error(error_msg)

        return {
            "ticker": ticker,
            "status": "error",
            "error": error_msg,
            "error_type": error_classification,
            "retryable": error_classification == "throttling"
        }


def classify_error(error_msg: str) -> str:
    """Classify error types to determine retry strategy."""
    error_lower = error_msg.lower()

    if "throttlingexception" in error_lower or "too many tokens" in error_lower:
        return "throttling"
    elif "timeout" in error_lower or "connection" in error_lower:
        return "network"
    elif "invalid" in error_lower or "not found" in error_lower:
        return "data"
    elif "permission" in error_lower or "access" in error_lower:
        return "auth"
    else:
        return "unknown"


def run_batch_analysis_with_retry(graph, tickers: List[str], date: str, max_workers: int = 4,
                                 max_total_time: int = 1800) -> Dict[str, Any]:
    """
    Run parallel analysis on list of tickers with intelligent retry for throttling errors.

    Args:
        graph: TradingAgentsGraph instance
        tickers: List of ticker symbols
        date: Analysis date
        max_workers: Number of parallel workers (will be reduced if throttling detected)
        max_total_time: Maximum total time in seconds to spend on analysis (default: 30 min)

    Returns:
        Dictionary with successful and failed analyses, plus retry statistics
    """
    if not tickers:
        return {"successful": {}, "failed": {}, "summary": "No tickers to analyze"}

    print(f"🚀 Running batch analysis on {len(tickers)} stocks with intelligent retry...")

    # Initialize batch state
    state = BatchAnalysisState()
    state.total_tickers = len(tickers)

    # Start timing
    start_time = time.time()
    current_workers = max_workers
    retry_round = 0

    # Initial analysis round
    print(f"📊 Round 1: Analyzing {len(tickers)} stocks with {current_workers} workers...")
    _run_single_batch_round(graph, tickers, date, state, current_workers)

    # Retry failed analyses if they're retryable
    while (not state.is_complete and
           time.time() - start_time < max_total_time and
           len(state.retry_queue) > 0):

        retry_round += 1

        # Wait for any ready retries and reduce concurrency to avoid throttling
        ready_retries = []
        while len(ready_retries) == 0 and len(state.retry_queue) > 0:
            ready_retries = state.get_ready_retries()
            if len(ready_retries) == 0:
                # Wait a bit for next retry window
                next_retry = min(task.next_retry_time for task in state.retry_queue)
                wait_time = next_retry - time.time()
                if wait_time > 0:
                    print(f"⏳ Waiting {wait_time:.0f}s for next retry window...")
                    time.sleep(min(wait_time, 10))  # Wait max 10s at a time

        if len(ready_retries) > 0:
            # Reduce workers by 50% each retry round to avoid further throttling
            current_workers = max(1, current_workers // 2)
            retry_tickers = [task.ticker for task in ready_retries]

            print(f"🔄 Round {retry_round + 1}: Retrying {len(retry_tickers)} failed stocks with {current_workers} workers...")
            _run_retry_round(graph, ready_retries, date, state, current_workers)

        # Check for timeout
        if time.time() - start_time > max_total_time:
            print(f"⏱️  Analysis timeout reached ({max_total_time}s), stopping retries...")
            break

    # Move any remaining retry tasks to permanent failures
    for task in state.retry_queue:
        state.add_permanent_failure(task.ticker, f"Max retries exceeded: {task.last_error}")

    total_time = time.time() - start_time
    retry_stats = {
        "total_rounds": retry_round + 1,
        "total_time": total_time,
        "final_workers": current_workers
    }

    return {
        "successful": state.successful,
        "failed": state.failed,
        "retry_stats": retry_stats,
        "summary": f"Analyzed {len(state.successful)}/{state.total_tickers} stocks successfully in {retry_stats['total_rounds']} rounds ({total_time:.0f}s)"
    }


def _run_single_batch_round(graph, tickers: List[str], date: str, state: BatchAnalysisState, workers: int):
    """Run a single round of batch analysis."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_ticker = {
            executor.submit(analyze_ticker_safe, graph, ticker, date): ticker
            for ticker in tickers
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            result = future.result()
            completed += 1

            progress = f"({completed}/{len(tickers)})"

            if result["status"] == "success":
                state.add_success(ticker, result)
                reasoning = result.get('report', '')
                reasoning_preview = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                print(f"✅ {ticker}: {result['decision']} {progress}")
                if reasoning_preview.strip():
                    print(f"   💭 Reasoning: {reasoning_preview}")
            else:
                # Check if retryable
                if result.get("retryable", False):
                    task = RetryableTask(ticker=ticker, date=date)
                    task.increment_attempt(result["error"])
                    state.add_retry(task)
                    print(f"🔄 {ticker}: Will retry after throttling cooldown {progress}")
                else:
                    state.add_permanent_failure(ticker, result["error"])
                    print(f"❌ {ticker}: {result['error']} {progress}")


def _run_retry_round(graph, retry_tasks: List[RetryableTask], date: str, state: BatchAnalysisState, workers: int):
    """Run a retry round for previously failed tasks."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit retry tasks
        future_to_task = {
            executor.submit(analyze_ticker_safe, graph, task.ticker, date): task
            for task in retry_tasks
        }

        # Collect results
        completed = 0
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            result = future.result()
            completed += 1

            progress = f"({completed}/{len(retry_tasks)})"

            if result["status"] == "success":
                state.add_success(task.ticker, result)
                reasoning = result.get('report', '')
                reasoning_preview = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                print(f"✅ {task.ticker}: {result['decision']} (retry success) {progress}")
                if reasoning_preview.strip():
                    print(f"   💭 Reasoning: {reasoning_preview}")
            else:
                # Check if can retry again
                if result.get("retryable", False) and task.should_retry():
                    task.increment_attempt(result["error"])
                    state.add_retry(task)
                    print(f"🔄 {task.ticker}: Will retry again (attempt {task.attempt + 1}) {progress}")
                else:
                    state.add_permanent_failure(task.ticker, result["error"])
                    print(f"❌ {task.ticker}: {result['error']} (max retries) {progress}")


def run_batch_analysis(graph, tickers: List[str], date: str, max_workers: int = 4) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Delegates to new retry-capable analysis function.
    """
    return run_batch_analysis_with_retry(graph, tickers, date, max_workers)


def display_results(results: Dict[str, Any], output_format: str = "summary") -> None:
    """Display batch analysis results with configurable output format."""
    successful = results["successful"]
    failed = results["failed"]
    retry_stats = results.get("retry_stats", {})

    print(f"\n📊 {results['summary']}")

    # Show retry statistics if available
    if retry_stats:
        print(f"\n🔄 Retry Statistics:")
        print(f"   • Total rounds: {retry_stats['total_rounds']}")
        print(f"   • Total time: {retry_stats['total_time']:.0f}s")
        print(f"   • Final workers: {retry_stats['final_workers']}")

    if successful:
        print(f"\n✅ Successful Analyses ({len(successful)}):")

        for ticker, result in successful.items():
            decision = result['decision']
            reasoning = result.get('report', '')

            print(f"\n📊 {ticker}: {decision}")

            if reasoning.strip():
                if output_format == "decisions":
                    # Show only decision, no reasoning
                    pass
                elif output_format == "detailed":
                    # Show full reasoning
                    print(f"   💭 Full Analysis:")
                    # Split reasoning into paragraphs for better readability
                    lines = reasoning.split('\n')
                    for line in lines:
                        if line.strip():
                            print(f"      {line}")
                else:  # summary (default)
                    # Show truncated reasoning
                    reasoning_summary = reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
                    print(f"   💭 Reasoning: {reasoning_summary}")

            print("   " + "─" * 50)

    if failed:
        print(f"\n❌ Failed Analyses ({len(failed)}):")
        for ticker, result in failed.items():
            error_msg = result['error']
            # Show if this was due to max retries
            if "Max retries exceeded" in error_msg:
                print(f"   {ticker}: {error_msg}")
            else:
                print(f"   {ticker}: {error_msg}")

    # Show completion statistics
    total = len(successful) + len(failed)
    success_rate = len(successful) / total * 100 if total > 0 else 0
    print(f"\n📈 Completion: {len(successful)}/{total} stocks ({success_rate:.1f}% success rate)")

    # Show usage hint for detailed output
    if output_format == "summary" and len(successful) > 0:
        print(f"\n💡 For full reasoning, use: python -m cli.main batch --output detailed")


# Main function for CLI integration
def batch_analyze_portfolio(graph, portfolio_file: str = "portfolio.json",
                          date: str = None, max_workers: int = 4,
                          max_total_time: int = None,
                          output_format: str = "summary") -> Dict[str, Any]:
    """
    Complete batch analysis workflow with intelligent retry for robust data collection.

    Args:
        graph: TradingAgentsGraph instance
        portfolio_file: Path to portfolio JSON file
        date: Analysis date (defaults to today if None)
        max_workers: Number of parallel workers (will adapt based on throttling)
        max_total_time: Maximum time in seconds for complete analysis (default: 30 min)

    Returns:
        Analysis results dictionary with retry statistics

    Note:
        This function ensures complete data collection by:
        - Automatically retrying throttled requests with exponential backoff
        - Reducing concurrency when throttling is detected
        - Only failing permanently on non-retryable errors
        - Providing detailed retry statistics for monitoring
    """
    if date is None:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")

    # Load configuration for retry behavior
    import os
    if max_total_time is None:
        max_total_time = int(os.getenv("BATCH_ANALYSIS_MAX_TIME", "1800"))  # 30 minutes default

    # Load tickers
    tickers = load_portfolio_tickers(portfolio_file)
    if not tickers:
        print(f"❌ No tickers found in {portfolio_file}")
        return {"successful": {}, "failed": {}, "summary": "No tickers to analyze"}

    print(f"📁 Loaded {len(tickers)} tickers from {portfolio_file}")
    print(f"🎯 Tickers: {', '.join(tickers)}")

    # Important: Use retry-capable analysis to ensure complete data collection
    results = run_batch_analysis_with_retry(graph, tickers, date, max_workers, max_total_time)

    # Display results with retry statistics
    display_results(results, output_format)

    # Ensure we got analysis for every ticker (critical for portfolio decisions)
    success_rate = len(results["successful"]) / len(tickers) if tickers else 0
    if success_rate < 1.0:
        print(f"\n⚠️  WARNING: Only {success_rate:.1%} of stocks analyzed successfully!")
        print(f"   Consider reviewing failed analyses before making portfolio decisions.")
        if success_rate < 0.5:
            print(f"   🚨 CRITICAL: Less than 50% success rate - recommend retrying analysis")

    return results