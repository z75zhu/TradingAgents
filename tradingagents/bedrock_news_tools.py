"""
Bedrock-powered news and analysis functions.
Enhanced with real data integration from Finnhub, Google News, and Reddit.
"""

from tradingagents.llm_providers import get_configured_llms
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.live_data_fetchers import live_finnhub, live_reddit
from tradingagents.dataflows.interface import get_google_news
from datetime import datetime, timedelta


def get_stock_news_bedrock(ticker, curr_date):
    """Enhanced Bedrock-powered stock news analysis with real data integration."""
    # Use the configured Bedrock LLM (quick thinking model for news analysis)
    quick_thinking_llm, _ = get_configured_llms(DEFAULT_CONFIG)
    llm = quick_thinking_llm

    # Gather real data from multiple sources
    real_data = []

    try:
        # 1. Get Finnhub news data
        end_date = curr_date
        start_date = (datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

        finnhub_news = live_finnhub.get_company_news(ticker, start_date, end_date)
        if finnhub_news and "Error" not in finnhub_news:
            real_data.append(f"=== FINNHUB NEWS DATA ===\n{finnhub_news}")

        # 2. Get Google News data
        google_news = get_google_news(ticker, curr_date)
        if google_news and "Error" not in google_news:
            real_data.append(f"=== GOOGLE NEWS DATA ===\n{google_news}")

        # 3. Get Reddit discussions
        reddit_discussions = live_reddit.get_stock_discussions(ticker, days_back=7)
        if reddit_discussions and "not available" not in reddit_discussions:
            real_data.append(f"=== REDDIT DISCUSSIONS ===\n{reddit_discussions}")

    except Exception as e:
        real_data.append(f"Note: Some data sources unavailable: {str(e)}")

    # Combine real data
    data_section = "\n\n".join(real_data) if real_data else "No real-time data available."

    prompt = f"""Analyze the following REAL market data for {ticker} around {curr_date} and provide comprehensive social media sentiment analysis.

=== REAL MARKET DATA ===
{data_section}

=== ANALYSIS INSTRUCTIONS ===
Based on the actual data provided above, analyze:

1. **News Sentiment Analysis**:
   - Overall sentiment from news headlines and content
   - Key themes and narratives emerging
   - Market-moving news and announcements

2. **Social Media Sentiment**:
   - Reddit community discussions and sentiment
   - Retail investor perception and mood
   - Social trading indicators and trends

3. **Market Impact Assessment**:
   - How the news/sentiment might affect stock price
   - Short-term vs long-term implications
   - Key catalysts or concerns identified

4. **Actionable Intelligence**:
   - Trading considerations based on sentiment
   - Risk factors from social sentiment
   - Opportunities identified from discussions

Provide a structured analysis with clear insights that can inform trading decisions. Focus on actionable intelligence rather than generic commentary."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Bedrock social media analysis unavailable: {str(e)}. Raw data available: {len(real_data)} sources"


def get_global_news_bedrock(curr_date):
    """Enhanced Bedrock-powered global news analysis with real data integration."""
    # Use the configured Bedrock LLM (quick thinking model for global news analysis)
    quick_thinking_llm, _ = get_configured_llms(DEFAULT_CONFIG)
    llm = quick_thinking_llm

    # Gather real market data
    real_data = []

    try:
        # 1. Get market indicators data
        market_indicators = live_finnhub.get_market_indicators()
        if market_indicators and "Error" not in market_indicators:
            real_data.append(f"=== MARKET INDICATORS ===\n{market_indicators}")

        # 2. Get sector performance
        sector_performance = live_finnhub.get_sector_performance()
        if sector_performance and "Error" not in sector_performance:
            real_data.append(f"=== SECTOR PERFORMANCE ===\n{sector_performance}")

        # 3. Get global market sentiment from Reddit
        market_sentiment = live_reddit.get_market_sentiment(days_back=7)
        if market_sentiment and "not available" not in market_sentiment:
            real_data.append(f"=== MARKET SENTIMENT ===\n{market_sentiment}")

        # 4. Get general economic news from Google
        economic_news = get_google_news("economy market federal reserve", curr_date)
        if economic_news and "Error" not in economic_news:
            real_data.append(f"=== ECONOMIC NEWS ===\n{economic_news}")

    except Exception as e:
        real_data.append(f"Note: Some data sources unavailable: {str(e)}")

    # Combine real data
    data_section = "\n\n".join(real_data) if real_data else "No real-time data available."

    prompt = f"""Analyze the following REAL market data for {curr_date} and provide comprehensive global macroeconomic analysis.

=== REAL MARKET DATA ===
{data_section}

=== ANALYSIS INSTRUCTIONS ===
Based on the actual market data provided above, analyze:

1. **Market Overview**:
   - Current market sentiment from major indices
   - VIX levels and volatility assessment
   - Overall market direction and trends

2. **Sector Analysis**:
   - Sector rotation patterns and performance
   - Leading and lagging sectors
   - Risk-on vs risk-off sentiment

3. **Macroeconomic Factors**:
   - Interest rate environment implications
   - Economic indicators and their market impact
   - Central bank policy considerations

4. **Global Risk Assessment**:
   - Geopolitical factors affecting markets
   - Currency and commodity trends
   - Systemic risks and opportunities

5. **Trading Implications**:
   - Portfolio positioning recommendations
   - Risk management considerations
   - Short-term vs long-term outlook

Provide actionable insights for trading decisions based on the real market data. Focus on concrete analysis rather than generic commentary."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Bedrock global news analysis unavailable: {str(e)}. Raw data available: {len(real_data)} sources"


def get_fundamentals_bedrock(ticker, curr_date):
    """Enhanced Bedrock-powered fundamental analysis with real data integration."""
    # Use the configured Bedrock LLM (deep thinking model for fundamental analysis)
    _, deep_thinking_llm = get_configured_llms(DEFAULT_CONFIG)
    llm = deep_thinking_llm

    # Gather real fundamental data
    real_data = []

    try:
        # 1. Get real-time stock quote
        stock_quote = live_finnhub.get_real_time_quote(ticker)
        if stock_quote and "Error" not in stock_quote:
            real_data.append(f"=== CURRENT STOCK DATA ===\n{stock_quote}")

        # 2. Get earnings data
        earnings_data = live_finnhub.get_earnings_data(ticker)
        if earnings_data and "Error" not in earnings_data:
            real_data.append(f"=== EARNINGS DATA ===\n{earnings_data}")

        # 3. Get analyst recommendations
        analyst_recs = live_finnhub.get_analyst_recommendations(ticker)
        if analyst_recs and "Error" not in analyst_recs:
            real_data.append(f"=== ANALYST RECOMMENDATIONS ===\n{analyst_recs}")

        # 4. Get insider transactions
        end_date = curr_date
        start_date = (datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")

        insider_data = live_finnhub.get_insider_transactions(ticker, start_date, end_date)
        if insider_data and "Error" not in insider_data:
            real_data.append(f"=== INSIDER ACTIVITY ===\n{insider_data}")

        # 5. Get company news for fundamental developments
        company_news = live_finnhub.get_company_news(ticker, start_date, end_date)
        if company_news and "Error" not in company_news:
            real_data.append(f"=== COMPANY NEWS ===\n{company_news}")

    except Exception as e:
        real_data.append(f"Note: Some data sources unavailable: {str(e)}")

    # Combine real data
    data_section = "\n\n".join(real_data) if real_data else "No real-time data available."

    prompt = f"""Analyze the following REAL fundamental data for {ticker} as of {curr_date} and provide comprehensive fundamental analysis.

=== REAL FUNDAMENTAL DATA ===
{data_section}

=== ANALYSIS INSTRUCTIONS ===
Based on the actual fundamental data provided above, analyze:

1. **Valuation Assessment**:
   - Current stock price vs intrinsic value indicators
   - Analyst consensus and target prices
   - Price momentum and technical levels

2. **Earnings Analysis**:
   - Recent earnings performance vs estimates
   - Earnings trends and growth patterns
   - Upcoming earnings expectations and catalysts

3. **Insider Activity Analysis**:
   - Insider buying/selling patterns
   - Management confidence indicators
   - Institutional activity implications

4. **Company Fundamentals**:
   - Business performance indicators from news
   - Competitive position and market share
   - Product developments and strategic initiatives

5. **Investment Thesis**:
   - Bull case supported by data
   - Bear case and risk factors
   - Key catalysts and events to monitor

6. **Trading Recommendations**:
   - Entry/exit price levels
   - Risk management considerations
   - Time horizon and position sizing

Provide actionable investment insights based on the real fundamental data. Focus on data-driven analysis and specific recommendations."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Bedrock fundamental analysis unavailable: {str(e)}. Raw data available: {len(real_data)} sources"