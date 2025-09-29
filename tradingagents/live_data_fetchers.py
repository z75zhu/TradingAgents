"""
Live data fetchers for Finnhub and Reddit APIs.
"""

import os
import praw
import finnhub
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class LiveFinnhubFetcher:
    """Fetches live data from Finnhub API."""

    def __init__(self, config=None):
        # Get API key from environment configuration
        if config:
            self.api_key = config.get("finnhub_api_key")
        else:
            from .env_config import get_env_config
            env_config = get_env_config()
            self.api_key = env_config.get("finnhub_api_key")

        if not self.api_key:
            print("Warning: FINNHUB_API_KEY not configured. Live data will be unavailable.")
            self.client = None
            return

        try:
            self.client = finnhub.Client(api_key=self.api_key)
            print(f"✅ Finnhub client initialized with API key: {self.api_key[:10]}...")
        except Exception as e:
            print(f"Error initializing Finnhub client: {e}")
            self.client = None

    def get_company_news(self, ticker: str, start_date: str, end_date: str) -> str:
        """
        Get live company news from Finnhub.

        Args:
            ticker: Stock ticker (e.g., 'AAPL')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Formatted string of news articles
        """
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            # Convert dates to datetime objects for API
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            # Finnhub company_news expects date strings, but let's try both formats
            try:
                # First try with date strings
                news = self.client.company_news(ticker, _from=start_date, to=end_date)
            except Exception as e1:
                # If that fails, try with Unix timestamps
                from_timestamp = int(start_dt.timestamp())
                to_timestamp = int(end_dt.timestamp())
                news = self.client.company_news(ticker, _from=from_timestamp, to=to_timestamp)

            if not news:
                return f"No news found for {ticker} between {start_date} and {end_date}"

            # Format the results
            formatted_news = []
            for article in news[:10]:  # Limit to 10 articles
                formatted_article = {
                    'headline': article.get('headline', 'N/A'),
                    'summary': article.get('summary', 'N/A'),
                    'source': article.get('source', 'N/A'),
                    'datetime': datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'url': article.get('url', 'N/A')
                }
                formatted_news.append(formatted_article)

            # Convert to readable format
            result = f"=== FINNHUB NEWS for {ticker} ({start_date} to {end_date}) ===\n\n"
            for i, article in enumerate(formatted_news, 1):
                result += f"{i}. {article['headline']}\n"
                result += f"   Source: {article['source']} | Date: {article['datetime']}\n"
                result += f"   Summary: {article['summary']}\n"
                result += f"   URL: {article['url']}\n\n"

            return result

        except Exception as e:
            return f"Error fetching Finnhub news for {ticker}: {str(e)}"

    def get_insider_transactions(self, ticker: str, start_date: str, end_date: str) -> str:
        """Get insider transactions from Finnhub."""
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            from_date = start_dt.strftime("%Y-%m-%d")
            to_date = end_dt.strftime("%Y-%m-%d")

            # Get insider transactions
            transactions = self.client.stock_insider_transactions(ticker, from_date, to_date)

            if not transactions or not transactions.get('data'):
                return f"No insider transactions found for {ticker} between {start_date} and {end_date}"

            result = f"=== INSIDER TRANSACTIONS for {ticker} ({start_date} to {end_date}) ===\n\n"

            for i, trans in enumerate(transactions['data'][:10], 1):  # Limit to 10 transactions
                result += f"{i}. {trans.get('name', 'N/A')} - {trans.get('title', 'N/A')}\n"
                result += f"   Transaction Date: {trans.get('transactionDate', 'N/A')}\n"
                result += f"   Shares: {trans.get('share', 'N/A')} | Price: ${trans.get('transactionPrice', 'N/A')}\n"
                result += f"   Transaction Code: {trans.get('transactionCode', 'N/A')}\n\n"

            return result

        except Exception as e:
            return f"Error fetching insider transactions for {ticker}: {str(e)}"

    def get_real_time_quote(self, ticker: str) -> str:
        """Get real-time stock quote from Finnhub."""
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            quote = self.client.quote(ticker)

            if not quote or 'c' not in quote:
                return f"No quote data available for {ticker}"

            result = f"=== REAL-TIME QUOTE for {ticker} ===\n\n"
            result += f"Current Price: ${quote.get('c', 'N/A')}\n"
            result += f"Change: ${quote.get('d', 'N/A')}\n"
            result += f"Percent Change: {quote.get('dp', 'N/A')}%\n"
            result += f"High: ${quote.get('h', 'N/A')}\n"
            result += f"Low: ${quote.get('l', 'N/A')}\n"
            result += f"Open: ${quote.get('o', 'N/A')}\n"
            result += f"Previous Close: ${quote.get('pc', 'N/A')}\n"
            result += f"Timestamp: {datetime.fromtimestamp(quote.get('t', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n"

            return result

        except Exception as e:
            return f"Error fetching real-time quote for {ticker}: {str(e)}"

    def get_earnings_data(self, ticker: str) -> str:
        """Get earnings data and estimates from Finnhub."""
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            result = f"=== EARNINGS DATA for {ticker} ===\n\n"

            # Try to get earnings calendar (this method exists)
            try:
                from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                to_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

                calendar = self.client.earnings_calendar(_from=from_date, to=to_date, symbol=ticker)

                if calendar and calendar.get('earningsCalendar'):
                    result += "Earnings Calendar:\n"
                    for i, earning in enumerate(calendar['earningsCalendar'][:5], 1):
                        result += f"{i}. Date: {earning.get('date', 'N/A')}\n"
                        result += f"   EPS Estimate: ${earning.get('epsEstimate', 'N/A')}\n"
                        result += f"   Revenue Estimate: ${earning.get('revenueEstimate', 'N/A')}\n"
                        result += f"   Revenue Actual: ${earning.get('revenueActual', 'N/A')}\n\n"
                else:
                    result += "No earnings calendar data available.\n"
            except Exception as e:
                result += f"Could not fetch earnings calendar: {str(e)}\n"

            # Try to get basic earnings (earnings surprises)
            try:
                surprises = self.client.earnings_surprises(ticker, limit=4)
                if surprises:
                    result += "\nRecent Earnings Surprises:\n"
                    for i, surprise in enumerate(surprises, 1):
                        result += f"{i}. Period: {surprise.get('period', 'N/A')}\n"
                        result += f"   Actual: ${surprise.get('actual', 'N/A')}\n"
                        result += f"   Estimate: ${surprise.get('estimate', 'N/A')}\n"
                        result += f"   Quarter: {surprise.get('quarter', 'N/A')}/{surprise.get('year', 'N/A')}\n\n"
            except Exception as e:
                result += f"Could not fetch earnings surprises: {str(e)}\n"

            return result

        except Exception as e:
            return f"Error fetching earnings data for {ticker}: {str(e)}"

    def get_analyst_recommendations(self, ticker: str) -> str:
        """Get analyst recommendations from Finnhub."""
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            recommendations = self.client.recommendation_trends(ticker)

            if not recommendations:
                return f"No analyst recommendations available for {ticker}"

            result = f"=== ANALYST RECOMMENDATIONS for {ticker} ===\n\n"

            for i, rec in enumerate(recommendations[:6], 1):  # Last 6 periods
                result += f"Period {i} ({rec.get('period', 'N/A')}):\n"
                result += f"   Strong Buy: {rec.get('strongBuy', 0)}\n"
                result += f"   Buy: {rec.get('buy', 0)}\n"
                result += f"   Hold: {rec.get('hold', 0)}\n"
                result += f"   Sell: {rec.get('sell', 0)}\n"
                result += f"   Strong Sell: {rec.get('strongSell', 0)}\n\n"

            return result

        except Exception as e:
            return f"Error fetching analyst recommendations for {ticker}: {str(e)}"

    def get_market_indicators(self) -> str:
        """Get general market indicators and indices."""
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            result = f"=== MARKET INDICATORS ===\n\n"

            # Major indices
            indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow, NASDAQ
            index_names = ["S&P 500", "Dow Jones", "NASDAQ"]

            for ticker, name in zip(indices, index_names):
                try:
                    quote = self.client.quote(ticker)
                    if quote and 'c' in quote:
                        result += f"{name}: ${quote.get('c', 'N/A')} "
                        result += f"({quote.get('dp', 'N/A')}%)\n"
                except:
                    continue

            # VIX Fear & Greed Index
            try:
                vix_quote = self.client.quote("^VIX")
                if vix_quote and 'c' in vix_quote:
                    result += f"\nVIX (Fear Index): {vix_quote.get('c', 'N/A')} "
                    result += f"({vix_quote.get('dp', 'N/A')}%)\n"
            except:
                pass

            return result

        except Exception as e:
            return f"Error fetching market indicators: {str(e)}"

    def get_sector_performance(self) -> str:
        """Get sector performance data."""
        if not self.client:
            return f"Finnhub API not available (no API key). Please set FINNHUB_API_KEY environment variable."

        try:
            result = f"=== SECTOR PERFORMANCE ===\n\n"

            # Common sector ETFs for performance tracking
            sectors = {
                "XLK": "Technology",
                "XLF": "Financial",
                "XLV": "Healthcare",
                "XLE": "Energy",
                "XLI": "Industrial",
                "XLY": "Consumer Discretionary",
                "XLP": "Consumer Staples",
                "XLU": "Utilities",
                "XLRE": "Real Estate"
            }

            for etf, sector_name in sectors.items():
                try:
                    quote = self.client.quote(etf)
                    if quote and 'c' in quote:
                        result += f"{sector_name} ({etf}): "
                        result += f"${quote.get('c', 'N/A')} "
                        result += f"({quote.get('dp', 'N/A')}%)\n"
                except:
                    continue

            return result

        except Exception as e:
            return f"Error fetching sector performance: {str(e)}"


class LiveRedditFetcher:
    """Fetches live data from Reddit API."""

    def __init__(self, config=None):
        # Get Reddit API credentials from environment configuration
        if config:
            client_id = config.get("reddit_client_id")
            client_secret = config.get("reddit_client_secret")
            user_agent = config.get("reddit_user_agent", "TradingAgents/1.0")
        else:
            from .env_config import get_env_config
            env_config = get_env_config()
            client_id = env_config.get("reddit_client_id")
            client_secret = env_config.get("reddit_client_secret")
            user_agent = env_config.get("reddit_user_agent", "TradingAgents/1.0")

        self.reddit = None

        if not client_id or not client_secret:
            print("Warning: Reddit API not configured. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET in .env file")
            return

        try:
            # Initialize Reddit client with environment credentials
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            # Test the connection
            self.reddit.user.me()
            print(f"✅ Reddit client initialized successfully")
        except Exception as e:
            print(f"Warning: Reddit API configuration issue: {e}")
            print("Please check your Reddit API credentials in .env file")
            self.reddit = None

    def get_stock_discussions(self, ticker: str, days_back: int = 7, max_posts: int = 10) -> str:
        """
        Get live Reddit discussions about a stock.

        Args:
            ticker: Stock ticker (e.g., 'AAPL')
            days_back: How many days back to search
            max_posts: Maximum number of posts to return

        Returns:
            Formatted string of Reddit discussions
        """
        if not self.reddit:
            return f"Reddit API not available. Please configure Reddit API credentials."

        try:
            # Search relevant subreddits
            subreddits = ['stocks', 'investing', 'SecurityAnalysis', 'ValueInvesting', 'StockMarket']

            all_posts = []
            search_query = f"{ticker}"

            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Search for posts containing the ticker
                    for post in subreddit.search(search_query, sort='new', time_filter='week', limit=5):
                        # Check if post is recent enough
                        post_date = datetime.fromtimestamp(post.created_utc)
                        if (datetime.now() - post_date).days <= days_back:
                            all_posts.append({
                                'title': post.title,
                                'subreddit': subreddit_name,
                                'score': post.score,
                                'num_comments': post.num_comments,
                                'created': post_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'url': f"https://reddit.com{post.permalink}",
                                'selftext': post.selftext[:200] + "..." if len(post.selftext) > 200 else post.selftext
                            })
                except Exception as e:
                    print(f"Error fetching from r/{subreddit_name}: {e}")
                    continue

            if not all_posts:
                return f"No recent Reddit discussions found for {ticker} in the last {days_back} days"

            # Sort by score (upvotes) and limit results
            all_posts.sort(key=lambda x: x['score'], reverse=True)
            all_posts = all_posts[:max_posts]

            # Format results
            result = f"=== REDDIT DISCUSSIONS for {ticker} (Last {days_back} days) ===\n\n"

            for i, post in enumerate(all_posts, 1):
                result += f"{i}. r/{post['subreddit']}: {post['title']}\n"
                result += f"   Score: {post['score']} | Comments: {post['num_comments']} | Date: {post['created']}\n"
                if post['selftext'].strip():
                    result += f"   Content: {post['selftext']}\n"
                result += f"   URL: {post['url']}\n\n"

            return result

        except Exception as e:
            return f"Error fetching Reddit discussions for {ticker}: {str(e)}"

    def get_market_sentiment(self, days_back: int = 7, max_posts: int = 15) -> str:
        """Get general market sentiment from Reddit."""
        if not self.reddit:
            return f"Reddit API not available. Please configure Reddit API credentials."

        try:
            # Get hot posts from market-related subreddits
            market_subreddits = ['stocks', 'investing', 'SecurityAnalysis', 'StockMarket', 'economics']

            all_posts = []

            for subreddit_name in market_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    for post in subreddit.hot(limit=5):
                        post_date = datetime.fromtimestamp(post.created_utc)
                        if (datetime.now() - post_date).days <= days_back:
                            all_posts.append({
                                'title': post.title,
                                'subreddit': subreddit_name,
                                'score': post.score,
                                'num_comments': post.num_comments,
                                'created': post_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'url': f"https://reddit.com{post.permalink}",
                                'selftext': post.selftext[:150] + "..." if len(post.selftext) > 150 else post.selftext
                            })
                except Exception as e:
                    print(f"Error fetching from r/{subreddit_name}: {e}")
                    continue

            if not all_posts:
                return f"No recent market discussions found on Reddit in the last {days_back} days"

            # Sort by score and limit
            all_posts.sort(key=lambda x: x['score'], reverse=True)
            all_posts = all_posts[:max_posts]

            # Format results
            result = f"=== REDDIT MARKET SENTIMENT (Last {days_back} days) ===\n\n"

            for i, post in enumerate(all_posts, 1):
                result += f"{i}. r/{post['subreddit']}: {post['title']}\n"
                result += f"   Score: {post['score']} | Comments: {post['num_comments']} | Date: {post['created']}\n"
                if post['selftext'].strip():
                    result += f"   Content: {post['selftext']}\n"
                result += f"   URL: {post['url']}\n\n"

            return result

        except Exception as e:
            return f"Error fetching Reddit market sentiment: {str(e)}"


# Initialize global instances with environment configuration
from .env_config import get_env_config
_env_config = get_env_config()

live_finnhub = LiveFinnhubFetcher(_env_config.get_config())
live_reddit = LiveRedditFetcher(_env_config.get_config())