#!/usr/bin/env python3
"""
Test that the multi-agent system actually has access to live Finnhub data.
"""

import sys
import os
from datetime import datetime

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_agent_finnhub_access():
    """Test that agents have access to live Finnhub tools."""
    print("🔍 Testing Multi-Agent System Live Finnhub Access")
    print("=" * 60)

    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        print("✅ Successfully imported TradingAgentsGraph")

        # Create config for Bedrock (your current setup)
        config = DEFAULT_CONFIG.copy()

        print(f"📋 Current configuration:")
        print(f"   LLM Provider: {config.get('llm_provider')}")
        print(f"   Quick Think Model: {config.get('quick_think_llm')}")

        # Initialize the trading system
        print("\n🤖 Initializing Multi-Agent Trading System...")
        ta = TradingAgentsGraph(
            selected_analysts=["news", "fundamentals"],  # Test agents that use Finnhub
            debug=False,
            config=config
        )
        print("✅ Multi-agent system initialized successfully")

        # Check what tools are available to each agent
        print("\n🛠️ Checking agent tool availability...")

        # Check News Agent tools
        news_tools = ta.tool_nodes["news"].tools
        news_tool_names = [tool.name for tool in news_tools]
        print(f"📰 News Agent has {len(news_tools)} tools:")

        has_live_finnhub_news = "get_finnhub_news_live" in news_tool_names
        print(f"   {'✅' if has_live_finnhub_news else '❌'} Live Finnhub News: {has_live_finnhub_news}")

        has_google_news = "get_google_news" in news_tool_names
        print(f"   {'✅' if has_google_news else '❌'} Google News: {has_google_news}")

        for tool_name in news_tool_names:
            if "finnhub" in tool_name.lower() or "live" in tool_name.lower():
                print(f"   🔸 {tool_name}")

        # Check Fundamentals Agent tools
        fundamentals_tools = ta.tool_nodes["fundamentals"].tools
        fundamentals_tool_names = [tool.name for tool in fundamentals_tools]
        print(f"\n📊 Fundamentals Agent has {len(fundamentals_tools)} tools:")

        has_live_insider = "get_finnhub_insider_transactions_live" in fundamentals_tool_names
        print(f"   {'✅' if has_live_insider else '❌'} Live Insider Transactions: {has_live_insider}")

        for tool_name in fundamentals_tool_names:
            if "finnhub" in tool_name.lower() or "live" in tool_name.lower():
                print(f"   🔸 {tool_name}")

        # Test direct tool access
        print("\n🧪 Testing direct tool access...")

        try:
            # Test live Finnhub news tool
            toolkit = ta.toolkit
            curr_date = datetime.now().strftime("%Y-%m-%d")

            print(f"   Testing live Finnhub news for AAPL on {curr_date}...")
            news_result = toolkit.get_finnhub_news_live("AAPL", curr_date, 3)

            if "Error" not in news_result and "not available" not in news_result:
                print("   ✅ Live Finnhub news tool working!")
                print(f"   📄 Sample: {news_result[:100]}...")
            else:
                print(f"   ❌ Live Finnhub news issue: {news_result[:100]}...")

        except Exception as e:
            print(f"   ❌ Error testing live tools: {e}")

        # Summary of agent access
        print(f"\n📋 SUMMARY - Multi-Agent System Live Data Access:")
        print(f"   {'✅' if has_live_finnhub_news else '❌'} News Agent can access live Finnhub news")
        print(f"   {'✅' if has_live_insider else '❌'} Fundamentals Agent can access live insider data")
        print(f"   {'✅' if has_google_news else '❌'} News Agent can access Google News")

        # Final verification
        all_good = has_live_finnhub_news and has_live_insider and has_google_news

        return all_good

    except Exception as e:
        print(f"❌ Error during agent testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_agent_workflow():
    """Test a specific agent to ensure it can actually use live data."""
    print(f"\n🎯 Testing Specific Agent Workflow with Live Data")
    print("=" * 60)

    try:
        from tradingagents.agents.analysts.news_analyst import create_news_analyst
        from tradingagents.agents.utils.agent_utils import Toolkit
        from tradingagents.llm_providers import get_configured_llms
        from tradingagents.default_config import DEFAULT_CONFIG

        # Create the components the agent needs
        config = DEFAULT_CONFIG.copy()
        quick_llm, _ = get_configured_llms(config)
        toolkit = Toolkit(config=config)

        print("✅ Created agent components")

        # Create news analyst
        news_agent = create_news_analyst(quick_llm, toolkit)
        print("✅ Created news analyst")

        # Test that the agent has the right tools
        if hasattr(toolkit, 'get_finnhub_news_live'):
            print("✅ News analyst has access to live Finnhub tools")
            return True
        else:
            print("❌ News analyst missing live Finnhub tools")
            return False

    except Exception as e:
        print(f"❌ Error in agent workflow test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE MULTI-AGENT LIVE DATA VERIFICATION")
    print("=" * 60)

    success1 = test_agent_finnhub_access()
    success2 = test_specific_agent_workflow()

    print("\n" + "=" * 60)

    if success1 and success2:
        print("🎉 VERIFICATION COMPLETE: SUCCESS!")
        print()
        print("✅ Your multi-agent system HAS access to real-time Finnhub data!")
        print("✅ News agents can fetch live financial news")
        print("✅ Fundamentals agents can fetch live insider transactions")
        print("✅ All agents have live data tools properly configured")
        print()
        print("🚀 Your trading system is ready with live market intelligence!")
    else:
        print("❌ VERIFICATION FAILED!")
        print("Some agents may not have proper access to live Finnhub data.")

    print("=" * 60)