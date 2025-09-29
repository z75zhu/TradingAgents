import functools
import time
import json


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        # Get portfolio context if available for position sizing
        portfolio_context = ""
        if "current_position" in state:
            current_shares = state.get("current_shares", 0)
            current_price = state.get("current_price", 0)
            if current_shares > 0:
                portfolio_context = f"\n\nCURRENT POSITION: You currently hold {current_shares} shares at ${current_price:.2f} per share."
            else:
                portfolio_context = f"\n\nNEW POSITION: No current position. Current price: ${current_price:.2f} per share."

        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions.

CRITICAL: You MUST provide specific share quantities in your recommendation.

Based on your analysis, provide a detailed recommendation including:
1. Your analysis and reasoning
2. Specific action (BUY/SELL/HOLD)
3. EXACT number of shares or percentage of position

Always end with this EXACT format:
FINAL TRANSACTION PROPOSAL: **[BUY/SELL/HOLD] [NUMBER] SHARES**

Examples:
- FINAL TRANSACTION PROPOSAL: **BUY 25 SHARES**
- FINAL TRANSACTION PROPOSAL: **SELL 50 SHARES**
- FINAL TRANSACTION PROPOSAL: **SELL ALL SHARES**
- FINAL TRANSACTION PROPOSAL: **HOLD CURRENT POSITION**

{portfolio_context}

Past trading lessons: {past_memory_str}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
