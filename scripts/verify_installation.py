#!/usr/bin/env python3
"""
TradingAgents Installation Verification Script

This script verifies that all required dependencies for TradingAgents
are properly installed, with special focus on technical analysis components.

Usage:
    python scripts/verify_installation.py
"""

import sys
import os
from typing import List, Tuple, Dict, Any

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major != 3:
        print("❌ Python 3.x required")
        return False

    if version.minor < 10:
        print("⚠️  Python 3.10+ recommended for best compatibility")
        return False

    print("✅ Python version compatible")
    return True

def check_core_dependencies() -> Dict[str, bool]:
    """Check core TradingAgents dependencies."""
    core_deps = [
        ('pandas', 'Data processing framework'),
        ('numpy', 'Numerical computing'),
        ('boto3', 'AWS Bedrock access'),
        ('langchain', 'LLM framework'),
        ('chromadb', 'Vector database'),
        ('finnhub', 'Financial data API'),
        ('praw', 'Reddit social media data'),
        ('requests', 'HTTP requests'),
        ('beautifulsoup4', 'Web scraping'),
        ('python_dotenv', 'Environment configuration'),
    ]

    results = {}
    print("\n📦 Core Dependencies:")

    for package, description in core_deps:
        try:
            # Handle special import names
            import_name = package
            if package == 'python_dotenv':
                import_name = 'dotenv'
            elif package == 'beautifulsoup4':
                import_name = 'bs4'

            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {package}: {version} - {description}")
            results[package] = True
        except ImportError:
            print(f"   ❌ {package}: NOT AVAILABLE - {description}")
            results[package] = False

    return results

def check_technical_analysis() -> Dict[str, bool]:
    """Check technical analysis specific dependencies."""
    print("\n📈 Technical Analysis Dependencies:")
    results = {}

    # Check TA-Lib (required for technical analysis)
    try:
        import talib
        version = getattr(talib, '__version__', 'unknown')
        functions_count = len(talib.get_functions())
        print(f"   ✅ TA-Lib: {version} - {functions_count} technical functions available")
        print("      → Candlestick patterns, indicators, overlap studies")
        results['talib'] = True
    except ImportError:
        print("   ❌ TA-Lib: NOT AVAILABLE - Required for technical analysis")
        print("      → Install: brew install ta-lib && pip install TA-Lib")
        results['talib'] = False

    # Check pandas-ta (optional, Python 3.12+ only)
    try:
        import pandas_ta
        version = getattr(pandas_ta, '__version__', 'unknown')
        print(f"   ✅ pandas-ta: {version} - Additional technical indicators")
        results['pandas_ta'] = True
    except ImportError:
        python_version = sys.version_info
        if python_version.minor >= 12:
            print("   ⚠️  pandas-ta: Available but not installed (optional)")
            print("      → Install: pip install pandas-ta")
        else:
            print("   ⚠️  pandas-ta: Not available (requires Python 3.12+)")
        results['pandas_ta'] = False

    return results

def check_environment_config() -> Dict[str, bool]:
    """Check environment configuration."""
    print("\n⚙️  Environment Configuration:")
    results = {}

    # Check for .env file
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        print("   ✅ .env file: Found")
        results['env_file'] = True
    else:
        print("   ⚠️  .env file: Not found")
        print("      → Copy .env.example to .env and configure")
        results['env_file'] = False

    # Check key environment variables
    required_vars = [
        ('AWS_PROFILE', 'AWS profile for Bedrock access'),
        ('AWS_REGION', 'AWS region'),
        ('FINNHUB_API_KEY', 'Finnhub API key for financial data'),
        ('LLM_PROVIDER', 'LLM provider configuration')
    ]

    for var, description in required_vars:
        if os.getenv(var):
            # Mask API keys for security
            value = os.getenv(var)
            if 'key' in var.lower() or 'secret' in var.lower():
                value = value[:8] + '...' if len(value) > 8 else '***'
            print(f"   ✅ {var}: {value} - {description}")
            results[var] = True
        else:
            print(f"   ⚠️  {var}: Not set - {description}")
            results[var] = False

    return results

def test_technical_analysis_functionality() -> bool:
    """Test that technical analysis functions work."""
    print("\n🧪 Technical Analysis Functionality Test:")

    try:
        from tradingagents.technical_patterns import TechnicalPatternAnalyzer
        print("   ✅ TechnicalPatternAnalyzer: Import successful")

        # Test basic functionality
        analyzer = TechnicalPatternAnalyzer()
        print("   ✅ TechnicalPatternAnalyzer: Initialization successful")

        # Test with sample data
        import pandas as pd
        import numpy as np

        # Create minimal test data
        dates = pd.date_range('2024-01-01', periods=30)
        prices = 100 + np.cumsum(np.random.randn(30) * 0.5)
        test_data = pd.DataFrame({
            'Date': dates,
            'Open': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': np.random.randint(100000, 1000000, 30)
        })

        summary = analyzer.generate_technical_summary(test_data)
        if 'error' not in summary:
            print("   ✅ Technical analysis: Pattern detection working")
            print(f"      → Sentiment: {summary.get('overall_sentiment', 'unknown')}")
            print(f"      → Confidence: {summary.get('confidence_score', 'unknown')}%")
        else:
            print(f"   ⚠️  Technical analysis: {summary['error']}")

        return True

    except Exception as e:
        print(f"   ❌ Technical analysis test failed: {e}")
        return False

def test_live_data_tools() -> bool:
    """Test that live data tools are available."""
    print("\n🌐 Live Data Tools Test:")

    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.default_config import DEFAULT_CONFIG

        toolkit = Toolkit(DEFAULT_CONFIG)
        print("   ✅ Toolkit: Import and initialization successful")

        # Check that live technical analysis tools exist
        live_tools = [
            'get_technical_analysis_report_online',
            'get_candlestick_patterns_online',
            'get_support_resistance_online',
            'get_fibonacci_analysis_online'
        ]

        for tool_name in live_tools:
            if hasattr(toolkit, tool_name):
                print(f"   ✅ {tool_name}: Available")
            else:
                print(f"   ❌ {tool_name}: Missing")
                return False

        # Verify offline tools are removed
        offline_tools = [
            'get_technical_analysis_report',
            'get_candlestick_patterns',
            'get_support_resistance',
            'get_fibonacci_analysis'
        ]

        for tool_name in offline_tools:
            if hasattr(toolkit, tool_name):
                print(f"   ❌ {tool_name}: Offline tool still present!")
                return False
            else:
                print(f"   ✅ {tool_name}: Offline tool properly removed")

        return True

    except Exception as e:
        print(f"   ❌ Live data tools test failed: {e}")
        return False

def generate_summary(all_results: Dict[str, Dict[str, bool]]) -> None:
    """Generate installation summary."""
    print("\n" + "="*60)
    print("📋 INSTALLATION SUMMARY")
    print("="*60)

    total_checks = sum(len(results) for results in all_results.values())
    passed_checks = sum(sum(results.values()) for results in all_results.values())

    print(f"Overall: {passed_checks}/{total_checks} checks passed")

    # Critical components
    critical_missing = []
    if not all_results.get('core', {}).get('boto3', True):
        critical_missing.append('boto3 (AWS Bedrock access)')
    if not all_results.get('core', {}).get('langchain', True):
        critical_missing.append('langchain (LLM framework)')
    if not all_results.get('technical', {}).get('talib', True):
        critical_missing.append('TA-Lib (technical analysis)')

    if critical_missing:
        print("\n❌ CRITICAL ISSUES:")
        for issue in critical_missing:
            print(f"   - {issue}")
        print("\nSystem may not function properly. Please install missing dependencies.")
    else:
        print("\n✅ ALL CRITICAL COMPONENTS INSTALLED")
        print("TradingAgents should work correctly.")

    # Optional components
    optional_missing = []
    if not all_results.get('technical', {}).get('pandas_ta', True):
        optional_missing.append('pandas-ta (enhanced technical indicators)')
    if not all_results.get('env', {}).get('env_file', True):
        optional_missing.append('.env configuration file')

    if optional_missing:
        print("\n⚠️  OPTIONAL IMPROVEMENTS:")
        for improvement in optional_missing:
            print(f"   - {improvement}")

    print(f"\n🚀 Ready to run: python -m cli.main analyze AAPL")
    print(f"📚 Documentation: README.md and docs/TECHNICAL_ANALYSIS_SETUP.md")

def main():
    """Run complete installation verification."""
    print("🔍 TradingAgents Installation Verification")
    print("=" * 50)

    all_results = {}

    # Basic checks
    check_python_version()
    all_results['core'] = check_core_dependencies()
    all_results['technical'] = check_technical_analysis()
    all_results['env'] = check_environment_config()

    # Functionality tests
    tech_test = test_technical_analysis_functionality()
    tools_test = test_live_data_tools()

    all_results['functionality'] = {
        'technical_analysis': tech_test,
        'live_data_tools': tools_test
    }

    # Summary
    generate_summary(all_results)

if __name__ == '__main__':
    main()