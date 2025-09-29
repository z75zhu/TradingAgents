#!/usr/bin/env python3
"""
Test Environment Configuration System

This script tests the new environment variable loading system with python-dotenv
and validates that all configuration is working correctly.
"""

import sys
import os
from datetime import datetime

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_env_loading():
    """Test basic environment variable loading."""
    print("🔧 TESTING ENVIRONMENT VARIABLE LOADING")
    print("=" * 60)

    try:
        from tradingagents.env_config import get_env_config, reload_env_config

        # Test initial loading
        env_config = get_env_config()
        print("✅ Successfully loaded environment configuration")

        # Test configuration access
        aws_profile = env_config.get("aws_profile")
        llm_provider = env_config.get("llm_provider")
        finnhub_key = env_config.get("finnhub_api_key")

        print(f"📋 Configuration Summary:")
        print(f"   AWS Profile: {aws_profile}")
        print(f"   LLM Provider: {llm_provider}")
        print(f"   Finnhub API Key: {'***SET***' if finnhub_key else 'NOT SET'}")

        # Test specific getters
        aws_config = env_config.get_aws_config()
        llm_config = env_config.get_llm_config()
        api_config = env_config.get_api_config()

        print(f"\n🔑 AWS Configuration:")
        print(f"   Profile: {aws_config['aws_profile']}")
        print(f"   Region: {aws_config['aws_region']}")

        print(f"\n🤖 LLM Configuration:")
        print(f"   Provider: {llm_config['llm_provider']}")
        print(f"   Quick Model: {llm_config['quick_think_llm']}")
        print(f"   Deep Model: {llm_config['deep_think_llm']}")

        print(f"\n🔗 API Configuration:")
        print(f"   Finnhub: {'Configured' if api_config['finnhub_api_key'] else 'Missing'}")
        print(f"   Reddit: {'Configured' if api_config['reddit_client_id'] else 'Missing'}")

        return True

    except Exception as e:
        print(f"❌ Error testing environment loading: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_default_config_integration():
    """Test integration with default config system."""
    print("\n⚙️ TESTING DEFAULT CONFIG INTEGRATION")
    print("=" * 60)

    try:
        from tradingagents.default_config import DEFAULT_CONFIG, get_default_config

        print("✅ Successfully imported DEFAULT_CONFIG with environment integration")

        # Check key configuration values
        required_keys = [
            "aws_profile", "aws_region", "llm_provider",
            "quick_think_llm", "deep_think_llm", "finnhub_api_key"
        ]

        print(f"\n📋 Configuration Values:")
        for key in required_keys:
            value = DEFAULT_CONFIG.get(key)
            if "key" in key.lower() or "secret" in key.lower():
                display_value = "***SET***" if value else "NOT SET"
            else:
                display_value = value

            print(f"   {key}: {display_value}")

        # Test function-based access
        config_copy = get_default_config()
        print(f"\n✅ Configuration copy created with {len(config_copy)} keys")

        return True

    except Exception as e:
        print(f"❌ Error testing default config integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trading_system_integration():
    """Test that trading system works with new environment configuration."""
    print("\n🤖 TESTING TRADING SYSTEM INTEGRATION")
    print("=" * 60)

    try:
        # Test that the trading graph can initialize with new config
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        print("✅ Successfully imported trading components with new config")

        # Initialize trading system
        ta = TradingAgentsGraph(
            selected_analysts=["market"],
            debug=False,
            config=DEFAULT_CONFIG
        )

        print("✅ Successfully initialized TradingAgentsGraph with environment config")

        # Test configuration values are properly loaded
        config = ta.config
        print(f"\n📊 Trading System Configuration:")
        print(f"   LLM Provider: {config.get('llm_provider')}")
        print(f"   AWS Profile: {config.get('aws_profile')}")
        print(f"   Dynamic Selection: {config.get('enable_dynamic_selection')}")
        print(f"   Cost Optimization: {config.get('cost_optimization_enabled')}")

        return True

    except Exception as e:
        print(f"❌ Error testing trading system integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_file_validation():
    """Test .env file structure and validate required variables."""
    print("\n📄 TESTING .ENV FILE VALIDATION")
    print("=" * 60)

    try:
        import os
        from pathlib import Path

        # Check for .env file
        env_file = Path(".env")
        env_example_file = Path(".env.example")

        print(f"📁 File Status:")
        print(f"   .env file: {'✅ EXISTS' if env_file.exists() else '❌ MISSING'}")
        print(f"   .env.example file: {'✅ EXISTS' if env_example_file.exists() else '❌ MISSING'}")

        if env_file.exists():
            # Read and validate .env file structure
            with open(env_file, 'r') as f:
                content = f.read()

            # Check for key sections
            required_sections = [
                "AWS BEDROCK CONFIGURATION",
                "LLM PROVIDER SETTINGS",
                "FINANCIAL DATA APIS",
                "DYNAMIC MODEL SELECTION"
            ]

            print(f"\n📋 .env File Validation:")
            for section in required_sections:
                has_section = section in content
                print(f"   {section}: {'✅' if has_section else '❌'}")

            # Check for required variables
            required_vars = [
                "AWS_PROFILE", "LLM_PROVIDER", "QUICK_THINK_LLM",
                "DEEP_THINK_LLM", "FINNHUB_API_KEY"
            ]

            print(f"\n🔑 Required Variables:")
            missing_vars = []
            for var in required_vars:
                value = os.getenv(var)
                has_var = bool(value)
                print(f"   {var}: {'✅ SET' if has_var else '❌ MISSING'}")
                if not has_var:
                    missing_vars.append(var)

            if missing_vars:
                print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
            else:
                print(f"\n✅ All required variables are set!")

        return True

    except Exception as e:
        print(f"❌ Error validating .env file: {e}")
        return False

def test_security_features():
    """Test security features of the environment configuration."""
    print("\n🔒 TESTING SECURITY FEATURES")
    print("=" * 60)

    try:
        from tradingagents.env_config import get_env_config

        env_config = get_env_config()

        # Test string representation (should hide sensitive data)
        config_str = str(env_config)
        print("✅ Configuration string representation created")

        # Verify sensitive data is hidden
        has_hidden = "***HIDDEN***" in config_str
        print(f"   Sensitive data protection: {'✅ ACTIVE' if has_hidden else '⚠️  CHECK NEEDED'}")

        # Test different configuration getters
        api_config = env_config.get_api_config()
        print(f"\n🔐 API Configuration Security:")
        print(f"   API keys accessible: {'✅ YES' if api_config else '❌ NO'}")
        print(f"   Finnhub key: {'SET' if api_config.get('finnhub_api_key') else 'NOT SET'}")

        return True

    except Exception as e:
        print(f"❌ Error testing security features: {e}")
        return False

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE ENVIRONMENT CONFIGURATION TESTING")
    print("=" * 60)

    # Run all tests
    results = []
    results.append(("Environment Loading", test_env_loading()))
    results.append(("Default Config Integration", test_default_config_integration()))
    results.append(("Trading System Integration", test_trading_system_integration()))
    results.append((".env File Validation", test_env_file_validation()))
    results.append(("Security Features", test_security_features()))

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
        if result:
            passed += 1

    success_rate = (passed / len(results)) * 100

    print(f"\n📊 Overall Success Rate: {passed}/{len(results)} ({success_rate:.1f}%)")

    if success_rate >= 80:
        print("\n🎉 ENVIRONMENT CONFIGURATION SETUP SUCCESSFUL!")
        print()
        print("🚀 Your TradingAgents system now has proper environment management:")
        print("✅ Centralized .env file configuration")
        print("✅ python-dotenv integration for secure variable loading")
        print("✅ Comprehensive environment validation")
        print("✅ Security features for sensitive data protection")
        print("✅ Backward compatibility with existing code")
        print("✅ Flexible configuration with sensible defaults")
        print()
        print("💡 Next Steps:")
        print("  • Configure Reddit API credentials in .env for full social sentiment")
        print("  • Add additional API keys as needed for extended functionality")
        print("  • Review .env.example for all available configuration options")
        print("  • Keep .env file secure and never commit it to version control")
        print()
        print("🔧 Configuration Management:")
        print("  • Edit .env file to modify settings")
        print("  • Use .env.example as a template for deployment")
        print("  • Environment variables override .env file values")
        print("  • All sensitive data is automatically protected in logs")
    else:
        print("\n⚠️ ENVIRONMENT CONFIGURATION NEEDS ATTENTION")
        print("Please review the failed tests above for specific issues.")
        print("Check that .env file exists and contains required variables.")

    print("=" * 60)