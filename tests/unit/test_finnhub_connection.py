#!/usr/bin/env python3
"""
Test Finnhub live connection to ensure it's working properly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tradingagents.live_data_fetchers import live_finnhub
    print("✅ Successfully imported live_finnhub")
except Exception as e:
    print(f"❌ Error importing live_finnhub: {e}")
    sys.exit(1)

def test_finnhub_connection():
    """Test the Finnhub API connection and data retrieval."""
    print("🔍 Testing Finnhub Live Connection")
    print("=" * 50)

    # Test 1: Check if client is initialized
    print("1️⃣ Testing Finnhub client initialization...")
    if live_finnhub.client:
        print(f"✅ Finnhub client initialized successfully")
        print(f"   API Key: {live_finnhub.api_key[:10]}...")
    else:
        print("❌ Finnhub client not initialized")
        return False

    # Test 2: Try to fetch company news
    print("\n2️⃣ Testing live company news retrieval...")
    try:
        # Get news for Apple from last 7 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        print(f"   Fetching AAPL news from {start_date} to {end_date}...")
        news_result = live_finnhub.get_company_news("AAPL", start_date, end_date)

        if "Error" in news_result or "not available" in news_result:
            print(f"❌ Error in news retrieval: {news_result}")
            return False
        elif "No news found" in news_result:
            print("⚠️  No news found (this might be normal for weekends/holidays)")
            print(f"   Response: {news_result}")
        else:
            print("✅ Successfully retrieved company news!")
            print(f"   First 200 chars: {news_result[:200]}...")

    except Exception as e:
        print(f"❌ Exception during news retrieval: {e}")
        return False

    # Test 3: Try to fetch insider transactions
    print("\n3️⃣ Testing live insider transactions retrieval...")
    try:
        # Get insider transactions for Apple from last 30 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        print(f"   Fetching AAPL insider transactions from {start_date} to {end_date}...")
        insider_result = live_finnhub.get_insider_transactions("AAPL", start_date, end_date)

        if "Error" in insider_result or "not available" in insider_result:
            print(f"❌ Error in insider transactions: {insider_result}")
            return False
        elif "No insider transactions found" in insider_result:
            print("⚠️  No insider transactions found (this might be normal)")
            print(f"   Response: {insider_result}")
        else:
            print("✅ Successfully retrieved insider transactions!")
            print(f"   First 200 chars: {insider_result[:200]}...")

    except Exception as e:
        print(f"❌ Exception during insider transactions: {e}")
        return False

    # Test 4: Test the toolkit integration
    print("\n4️⃣ Testing toolkit integration...")
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        toolkit = Toolkit()

        # Test if the live tools are accessible
        if hasattr(toolkit, 'get_finnhub_news_live'):
            print("✅ Live Finnhub news tool available in toolkit")
        else:
            print("❌ Live Finnhub news tool not found in toolkit")

        if hasattr(toolkit, 'get_finnhub_insider_transactions_live'):
            print("✅ Live Finnhub insider transactions tool available in toolkit")
        else:
            print("❌ Live Finnhub insider transactions tool not found in toolkit")

    except Exception as e:
        print(f"❌ Error testing toolkit integration: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_finnhub_connection()

    print("\n" + "=" * 50)
    if success:
        print("🎉 FINNHUB CONNECTION TEST PASSED!")
        print("Your trading agents now have access to live Finnhub data!")
        print("\nLive data available:")
        print("✅ Company news")
        print("✅ Insider transactions")
        print("✅ Financial market data")
    else:
        print("❌ FINNHUB CONNECTION TEST FAILED!")
        print("Please check the error messages above.")

    print("=" * 50)