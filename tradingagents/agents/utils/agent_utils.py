from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import tradingagents.dataflows.interface as interface
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage
from tradingagents.bedrock_news_tools import (
    get_stock_news_bedrock,
    get_global_news_bedrock,
    get_fundamentals_bedrock
)
from tradingagents.live_data_fetchers import live_finnhub, live_reddit
from tradingagents.dataflows.talib_utils import (
    get_technical_analysis_report,
    get_candlestick_patterns_report,
    get_support_resistance_report,
    get_fibonacci_levels_report
)


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """
        
        global_news_result = interface.get_reddit_global_news(curr_date, 7, 5)

        return global_news_result

    @staticmethod
    @tool
    def get_finnhub_news(
        ticker: Annotated[
            str,
            "Search query of a company, e.g. 'AAPL, TSM, etc.",
        ],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock from Finnhub within a date range
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing news about the company within the date range from start_date to end_date
        """

        end_date_str = end_date

        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        look_back_days = (end_date - start_date).days

        finnhub_news_result = interface.get_finnhub_news(
            ticker, end_date_str, look_back_days
        )

        return finnhub_news_result

    @staticmethod
    @tool
    def get_reddit_stock_info(
        ticker: Annotated[
            str,
            "Ticker of a company. e.g. AAPL, TSM",
        ],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given stock from Reddit, given the current date.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted dataframe containing the latest news about the company on the given date
        """

        stock_news_results = interface.get_reddit_company_news(ticker, curr_date, 7, 5)

        return stock_news_results

    @staticmethod
    @tool
    def get_YFin_data(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_YFin_data_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data_online(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_stockstats_indicators_report(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, False
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_stockstats_indicators_report_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, True
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_finnhub_company_insider_sentiment(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[
            str,
            "current date of you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider sentiment information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the sentiment in the past 30 days starting at curr_date
        """

        data_sentiment = interface.get_finnhub_company_insider_sentiment(
            ticker, curr_date, 30
        )

        return data_sentiment

    @staticmethod
    @tool
    def get_finnhub_company_insider_transactions(
        ticker: Annotated[str, "ticker symbol"],
        curr_date: Annotated[
            str,
            "current date you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider transaction information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's insider transactions/trading information in the past 30 days
        """

        data_trans = interface.get_finnhub_company_insider_transactions(
            ticker, curr_date, 30
        )

        return data_trans

    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = interface.get_google_news(query, curr_date, 7)

        return google_news_results


    @staticmethod
    @tool
    def get_stock_news_bedrock(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve and analyze the latest social media sentiment for a given stock using Bedrock Claude.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted analysis of social media sentiment and discussions about the company.
        """

        bedrock_news_results = get_stock_news_bedrock(ticker, curr_date)
        return bedrock_news_results

    @staticmethod
    @tool
    def get_global_news_bedrock(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve and analyze the latest global macroeconomic news using Bedrock Claude.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted analysis of global macroeconomic news and trends.
        """

        bedrock_news_results = get_global_news_bedrock(curr_date)
        return bedrock_news_results

    @staticmethod
    @tool
    def get_fundamentals_bedrock(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve and analyze fundamental information about a given stock using Bedrock Claude.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A comprehensive fundamental analysis of the company.
        """

        bedrock_fundamentals_results = get_fundamentals_bedrock(ticker, curr_date)
        return bedrock_fundamentals_results

    @staticmethod
    @tool
    def get_finnhub_news_live(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"] = 7,
    ):
        """
        Retrieve live news about a company from Finnhub API.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date in yyyy-mm-dd format
            look_back_days (int): how many days to look back, default is 7
        Returns:
            str: formatted news articles from Finnhub
        """
        from datetime import datetime, timedelta

        end_date = curr_date
        start_date_dt = datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)
        start_date = start_date_dt.strftime("%Y-%m-%d")

        result = live_finnhub.get_company_news(ticker, start_date, end_date)
        return result

    @staticmethod
    @tool
    def get_finnhub_insider_transactions_live(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ):
        """
        Retrieve live insider transactions from Finnhub API.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date in yyyy-mm-dd format
            look_back_days (int): how many days to look back, default is 30
        Returns:
            str: formatted insider transaction data from Finnhub
        """
        from datetime import datetime, timedelta

        end_date = curr_date
        start_date_dt = datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)
        start_date = start_date_dt.strftime("%Y-%m-%d")

        result = live_finnhub.get_insider_transactions(ticker, start_date, end_date)
        return result

    @staticmethod
    @tool
    def get_reddit_stock_discussions_live(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        days_back: Annotated[int, "how many days to look back"] = 7,
    ):
        """
        Retrieve live Reddit discussions about a specific stock.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date in yyyy-mm-dd format (for reference)
            days_back (int): how many days to look back, default is 7
        Returns:
            str: formatted Reddit discussions about the stock
        """
        result = live_reddit.get_stock_discussions(ticker, days_back)
        return result

    @staticmethod
    @tool
    def get_reddit_market_sentiment_live(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        days_back: Annotated[int, "how many days to look back"] = 7,
    ):
        """
        Retrieve live Reddit market sentiment and discussions.
        Args:
            curr_date (str): current date in yyyy-mm-dd format (for reference)
            days_back (int): how many days to look back, default is 7
        Returns:
            str: formatted Reddit market sentiment and discussions
        """
        result = live_reddit.get_market_sentiment(days_back)
        return result

    @staticmethod
    @tool
    def get_finnhub_real_time_quote(
        ticker: Annotated[str, "ticker symbol for the company"],
    ):
        """
        Get real-time stock quote data from Finnhub.
        Args:
            ticker (str): ticker symbol of the company
        Returns:
            str: formatted real-time quote data including current price, changes, highs, lows
        """
        result = live_finnhub.get_real_time_quote(ticker)
        return result

    @staticmethod
    @tool
    def get_finnhub_earnings_data(
        ticker: Annotated[str, "ticker symbol for the company"],
    ):
        """
        Get earnings data and estimates from Finnhub.
        Args:
            ticker (str): ticker symbol of the company
        Returns:
            str: formatted earnings data including recent earnings and upcoming earnings calendar
        """
        result = live_finnhub.get_earnings_data(ticker)
        return result

    @staticmethod
    @tool
    def get_finnhub_analyst_recommendations(
        ticker: Annotated[str, "ticker symbol for the company"],
    ):
        """
        Get analyst recommendations from Finnhub.
        Args:
            ticker (str): ticker symbol of the company
        Returns:
            str: formatted analyst recommendations including buy/hold/sell ratings
        """
        result = live_finnhub.get_analyst_recommendations(ticker)
        return result

    @staticmethod
    @tool
    def get_finnhub_market_indicators(
    ):
        """
        Get general market indicators and major indices.
        Returns:
            str: formatted market indicators including S&P 500, Dow Jones, NASDAQ, and VIX
        """
        result = live_finnhub.get_market_indicators()
        return result

    @staticmethod
    @tool
    def get_finnhub_sector_performance(
    ):
        """
        Get sector performance data using sector ETFs.
        Returns:
            str: formatted sector performance data across major market sectors
        """
        result = live_finnhub.get_sector_performance()
        return result


    @staticmethod
    @tool
    def get_technical_analysis_report_online(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, yyyy-mm-dd"],
        lookback_days: Annotated[int, "days of data to analyze"] = 100,
    ):
        """
        Generate comprehensive technical analysis report using live data including candlestick patterns,
        support/resistance levels, Fibonacci analysis, and trading signals.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date for analysis, yyyy-mm-dd
            lookback_days (int): days of historical data to analyze, default 100
        Returns:
            str: comprehensive technical analysis report with patterns, levels, and signals
        """
        result = get_technical_analysis_report(ticker, curr_date, lookback_days, True)
        return result


    @staticmethod
    @tool
    def get_candlestick_patterns_online(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, yyyy-mm-dd"],
        lookback_days: Annotated[int, "days of data for pattern analysis"] = 30,
    ):
        """
        Detect and analyze candlestick patterns using live data for reversal and continuation signals.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date for analysis, yyyy-mm-dd
            lookback_days (int): days of data for pattern analysis, default 30
        Returns:
            str: candlestick pattern analysis with pattern types, reliability, and implications
        """
        result = get_candlestick_patterns_report(ticker, curr_date, lookback_days, True)
        return result


    @staticmethod
    @tool
    def get_support_resistance_online(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, yyyy-mm-dd"],
        lookback_days: Annotated[int, "days for level calculation"] = 50,
    ):
        """
        Calculate dynamic support and resistance levels using live data with trading implications.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date for analysis, yyyy-mm-dd
            lookback_days (int): days of data for level calculation, default 50
        Returns:
            str: support and resistance analysis with levels, distances, and trading implications
        """
        result = get_support_resistance_report(ticker, curr_date, lookback_days, True)
        return result


    @staticmethod
    @tool
    def get_fibonacci_analysis_online(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[str, "current date for analysis, yyyy-mm-dd"],
        trend_window: Annotated[int, "days to determine trend extremes"] = 50,
    ):
        """
        Calculate Fibonacci retracement levels using live data and identify key price zones.
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date for analysis, yyyy-mm-dd
            trend_window (int): days to determine trend high/low points, default 50
        Returns:
            str: Fibonacci retracement analysis with key levels and nearby zones
        """
        result = get_fibonacci_levels_report(ticker, curr_date, trend_window, True)
        return result
