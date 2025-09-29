#!/usr/bin/env python3
"""
TradingAgents Test Runner

Organized test execution for the TradingAgents project with proper categorization.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Add the parent directory to sys.path to import tradingagents
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


class TestRunner:
    """Manages and executes tests in the organized test structure."""

    def __init__(self):
        self.project_root = project_root
        self.tests_dir = self.project_root / "tests"

    def list_tests(self) -> dict:
        """List all available tests by category."""
        test_categories = {
            "unit": [],
            "integration": [],
            "system": []
        }

        for category in test_categories.keys():
            category_dir = self.tests_dir / category
            if category_dir.exists():
                test_files = list(category_dir.glob("test_*.py"))
                test_categories[category] = [f.name for f in test_files]

        return test_categories

    def run_test_file(self, test_file: Path) -> bool:
        """Run a single test file and return success status."""
        print(f"🧪 Running: {test_file.name}")
        print("=" * 60)

        try:
            # Change to project root for consistent imports
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            success = result.returncode == 0
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{test_file.name}: {status}")
            return success

        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT: {test_file.name} exceeded 5 minute limit")
            return False
        except Exception as e:
            print(f"❌ ERROR running {test_file.name}: {e}")
            return False

    def run_category(self, category: str) -> tuple:
        """Run all tests in a specific category."""
        category_dir = self.tests_dir / category
        if not category_dir.exists():
            print(f"❌ Category '{category}' not found")
            return 0, 0

        test_files = list(category_dir.glob("test_*.py"))
        if not test_files:
            print(f"📭 No test files found in '{category}' category")
            return 0, 0

        print(f"🚀 Running {category.upper()} Tests")
        print("=" * 60)

        passed = 0
        total = len(test_files)

        for test_file in sorted(test_files):
            if self.run_test_file(test_file):
                passed += 1
            print()  # Add spacing between tests

        return passed, total

    def run_all_tests(self) -> dict:
        """Run all tests in order: unit → integration → system."""
        results = {}
        categories = ["unit", "integration", "system"]

        for category in categories:
            passed, total = self.run_category(category)
            results[category] = {"passed": passed, "total": total}

        return results

    def print_summary(self, results: dict):
        """Print a comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        total_passed = 0
        total_tests = 0

        for category, result in results.items():
            passed = result["passed"]
            total = result["total"]
            success_rate = (passed / total * 100) if total > 0 else 0

            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"{status} {category.upper():12} {passed:2}/{total:2} ({success_rate:5.1f}%)")

            total_passed += passed
            total_tests += total

        overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_status = "✅" if total_passed == total_tests else "⚠️" if total_passed > 0 else "❌"

        print("-" * 60)
        print(f"{overall_status} OVERALL:     {total_passed:2}/{total_tests:2} ({overall_rate:5.1f}%)")

        if total_passed == total_tests:
            print("\n🎉 All tests passed! Your TradingAgents system is ready.")
        elif total_passed > 0:
            print("\n⚠️ Some tests failed. Review the output above for details.")
        else:
            print("\n❌ All tests failed. Check your environment configuration.")

        print("=" * 60)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="TradingAgents Test Runner")
    parser.add_argument(
        "--category", "-c",
        choices=["unit", "integration", "system", "all"],
        default="all",
        help="Test category to run (default: all)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available tests"
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.list:
        print("📋 Available Tests:")
        test_categories = runner.list_tests()
        for category, tests in test_categories.items():
            print(f"\n{category.upper()}:")
            for test in tests:
                print(f"  - {test}")
        return

    print("🧪 TRADINGAGENTS TEST RUNNER")
    print("=" * 60)

    if args.category == "all":
        results = runner.run_all_tests()
        runner.print_summary(results)
    else:
        passed, total = runner.run_category(args.category)
        results = {args.category: {"passed": passed, "total": total}}
        runner.print_summary(results)


if __name__ == "__main__":
    main()