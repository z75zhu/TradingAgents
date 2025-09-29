"""
Technical Analyst Agent for TradingAgents

This agent specializes in technical analysis, candlestick patterns, and chart-based
trading signals. It works alongside other analysts to provide comprehensive
technical perspective for trading decisions.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_technical_analyst(llm, toolkit):
    """
    Create a technical analyst agent node for the TradingAgents graph.

    This agent focuses on:
    - Candlestick pattern recognition
    - Support and resistance analysis
    - Fibonacci retracements
    - Technical trend analysis
    - Risk assessment from technical perspective

    Args:
        llm: Language model for the agent
        toolkit: Tool collection for data access

    Returns:
        Technical analyst node function
    """

    def technical_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state.get("company_name", ticker)

        # CRITICAL: Technical analysis ALWAYS uses live data - no offline mode
        # K-line patterns, support/resistance, and volume data are extremely time-sensitive
        # and change throughout the trading day, making live data essential
        tools = [
            toolkit.get_YFin_data_online,
            toolkit.get_technical_analysis_report_online,
            toolkit.get_candlestick_patterns_online,
            toolkit.get_support_resistance_online,
            toolkit.get_fibonacci_analysis_online,
            toolkit.get_stockstats_indicators_report_online,
        ]

        system_message = f"""You are a Technical Analysis Specialist for the TradingAgents multi-agent trading system. Your expertise is in chart patterns, price action analysis, and technical indicators. You work collaboratively with other specialists (Market Analyst, Fundamentals Analyst, News Analyst, Social Media Analyst) to provide comprehensive trading insights.

## Your Core Expertise

**Pattern Recognition:**
- Candlestick patterns (reversal, continuation, indecision patterns)
- Chart patterns (triangles, flags, head & shoulders, etc.)
- Multi-timeframe pattern confluence
- Pattern strength assessment and reliability scoring

**Technical Levels:**
- Dynamic support and resistance identification
- Fibonacci retracement and extension levels
- Key psychological price levels
- Breakout and breakdown analysis

**Trend Analysis:**
- Trend identification across timeframes
- Momentum analysis using technical indicators
- Volume confirmation and divergence analysis
- Risk/reward technical projections

**Risk Management:**
- Technical stop-loss level identification
- Position sizing based on technical volatility
- Entry and exit timing optimization
- Risk assessment using technical patterns

## Analysis Framework

1. **Start with Price Data:** Always get recent OHLCV data first using get_YFin_data_online
2. **Comprehensive Technical Analysis:** Use get_technical_analysis_report_online for full technical overview
3. **Pattern Deep Dive:** Use get_candlestick_patterns_online for specific pattern analysis
4. **Level Analysis:** Use get_support_resistance_online and get_fibonacci_analysis_online for key levels
5. **Indicator Confirmation:** Use get_stockstats_indicators_report_online for momentum/trend confirmation

## Key Technical Indicators to Consider

**Trend & Momentum:**
- Moving averages (20, 50, 200 SMA/EMA) for trend direction
- MACD for momentum shifts and divergence
- RSI for overbought/oversold conditions and divergence
- Volume indicators for confirmation

**Volatility & Risk:**
- Bollinger Bands for volatility and mean reversion
- ATR for stop-loss placement and position sizing
- Support/resistance distance for risk assessment

## Reporting Guidelines

**Structure your analysis as:**

1. **Technical Overview** - Current trend, key levels, overall technical sentiment
2. **Pattern Analysis** - Recent candlestick patterns and their implications
3. **Level Analysis** - Critical support/resistance and Fibonacci levels
4. **Momentum Assessment** - Technical indicator signals and confirmations
5. **Risk Assessment** - Technical risk factors and stop-loss recommendations
6. **Trading Signals** - Specific technical entry/exit signals and timing
7. **Technical Summary Table** - Key metrics organized for quick reference

**Critical Guidelines:**
- Always provide specific price levels for support, resistance, and key Fibonacci levels
- Include confidence scores for technical patterns (reliability percentages)
- Consider multiple timeframes when assessing patterns and trends
- Integrate volume analysis for pattern and breakout confirmation
- Provide actionable technical entry/exit levels with risk management

**Risk Management Focus:**
- Identify technical stop-loss levels based on pattern invalidation
- Assess risk/reward ratios using technical levels
- Consider market volatility (ATR) for position sizing recommendations
- Flag high-risk technical setups or deteriorating technical conditions

**Multi-Agent Collaboration:**
- Your technical analysis will be combined with fundamental, news, and sentiment analysis
- Provide technical confirmation or contradiction of other analysts' findings
- Focus on timing aspects that complement fundamental analysis
- Highlight when technical and fundamental analysis align or diverge

**Output Format:**
Provide detailed technical analysis with specific price levels, pattern descriptions, and clear trading signals. Include a summary table with key technical metrics. Be precise about technical levels and their significance for trading decisions.

The current date is {current_date} and you are analyzing {company_name} ({ticker}). Focus on actionable technical analysis that helps with trading timing and risk management."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        # Initialize technical report
        technical_report = ""

        # Process tool calls if any
        if len(result.tool_calls) == 0:
            technical_report = result.content

        return {
            "messages": [result],
            "technical_report": technical_report,
        }

    return technical_analyst_node


def create_technical_bull_researcher(llm, toolkit):
    """
    Create a technical bull researcher for debate scenarios.
    Focuses on bullish technical signals and patterns.
    """

    def technical_bull_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # Technical analysis ALWAYS uses live data - no offline mode
        tools = [
            toolkit.get_technical_analysis_report_online,
            toolkit.get_candlestick_patterns_online,
            toolkit.get_support_resistance_online,
            toolkit.get_fibonacci_analysis_online,
        ]

        system_message = f"""You are a Technical Bull Researcher in the TradingAgents debate system. Your role is to find and present the strongest bullish technical arguments for {ticker}.

## Your Mission
Identify and argue for bullish technical signals including:

**Bullish Patterns:**
- Hammer, Morning Star, Piercing Pattern, Bullish Engulfing
- Three White Soldiers, Ascending triangles, Bull flags
- Bullish divergence in RSI, MACD
- Golden cross formations in moving averages

**Bullish Levels:**
- Support level holds and bounces
- Fibonacci retracement support at key levels (38.2%, 50%, 61.8%)
- Breakout above resistance levels
- Volume confirmation on bullish moves

**Bullish Momentum:**
- RSI recovering from oversold conditions
- MACD bullish crossover and positive histogram
- Price above key moving averages
- Increasing volume on up moves

**Risk Management (Bullish Perspective):**
- Strong support levels limiting downside risk
- Favorable risk/reward ratios for long positions
- Technical patterns with high success rates

Focus only on legitimate bullish technical signals. Present them persuasively but accurately. The current date is {current_date}."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a technical analyst focused on finding bullish signals and patterns."
                    " Use the provided tools to identify strong technical reasons to be optimistic about the stock."
                    " Present your findings persuasively but accurately."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        return {"messages": [result]}

    return technical_bull_node


def create_technical_bear_researcher(llm, toolkit):
    """
    Create a technical bear researcher for debate scenarios.
    Focuses on bearish technical signals and patterns.
    """

    def technical_bear_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # Technical analysis ALWAYS uses live data - no offline mode
        tools = [
            toolkit.get_technical_analysis_report_online,
            toolkit.get_candlestick_patterns_online,
            toolkit.get_support_resistance_online,
            toolkit.get_fibonacci_analysis_online,
        ]

        system_message = f"""You are a Technical Bear Researcher in the TradingAgents debate system. Your role is to find and present the strongest bearish technical arguments for {ticker}.

## Your Mission
Identify and argue for bearish technical signals including:

**Bearish Patterns:**
- Hanging Man, Evening Star, Dark Cloud Cover, Bearish Engulfing
- Three Black Crows, Descending triangles, Bear flags
- Bearish divergence in RSI, MACD
- Death cross formations in moving averages

**Bearish Levels:**
- Resistance level holds and rejects price
- Failed breakout attempts above key resistance
- Break below critical support levels
- Fibonacci resistance at key levels preventing advances

**Bearish Momentum:**
- RSI showing overbought conditions or negative divergence
- MACD bearish crossover and negative histogram
- Price below key moving averages with downward slope
- Distribution patterns with high volume on down moves

**Risk Management (Bearish Perspective):**
- Weak support levels offering little downside protection
- Poor risk/reward ratios for long positions
- Technical breakdown patterns with high failure rates

Focus only on legitimate bearish technical signals. Present them persuasively but accurately. The current date is {current_date}."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a technical analyst focused on finding bearish signals and patterns."
                    " Use the provided tools to identify strong technical reasons to be cautious about the stock."
                    " Present your findings persuasively but accurately."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        return {"messages": [result]}

    return technical_bear_node