import pandas as pd
import yfinance as yf
from stockstats import wrap
from typing import Annotated
import os
from ..default_config import DEFAULT_CONFIG

def get_config():
    """Get configuration - simplified for Bedrock-only architecture."""
    return DEFAULT_CONFIG.copy()
from .cache_utils import get_smart_cache, create_cache_key


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the stock data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = False,
    ):
        df = None
        data = None

        if not online:
            try:
                data = pd.read_csv(
                    os.path.join(
                        data_dir,
                        f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                    )
                )
                df = wrap(data)
            except FileNotFoundError:
                raise Exception("Stockstats fail: Yahoo Finance data not fetched yet!")
        else:
            # Online data fetching with smart caching
            today_date = pd.Timestamp.today()
            curr_date_dt = pd.to_datetime(curr_date)

            end_date = today_date
            start_date = today_date - pd.DateOffset(years=15)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            curr_date_str = curr_date_dt.strftime("%Y-%m-%d")

            # CRITICAL: Determine if this is time-sensitive data
            is_current_day = curr_date_dt.date() == today_date.date()
            data_source = "stock_price_current_day" if is_current_day else "stock_price_historical"

            # Never cache current-day data - always fetch live
            if is_current_day:
                print(f"🔴 Current-day data requested for {symbol} - bypassing cache entirely")

            # Create cache key for this request
            cache_key = create_cache_key(
                data_source=data_source,
                symbol=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                indicator=indicator
            )

            # Initialize smart cache
            smart_cache = get_smart_cache()

            # Check if we should use cache and if cache is valid
            use_cache = False
            if not is_current_day:  # Only consider caching for historical data
                use_cache = smart_cache.should_use_cache(
                    data_source=data_source,
                    date_str=curr_date_str,
                    cache_key=cache_key
                )

            data = None
            if use_cache:
                # Try to get cached data
                cached_data = smart_cache.get_cached_data(cache_key)
                if cached_data is not None:
                    try:
                        # Load from cache (CSV format)
                        if isinstance(cached_data, str):
                            import io
                            data = pd.read_csv(io.StringIO(cached_data))
                            data["Date"] = pd.to_datetime(data["Date"])
                            print(f"🔄 Using cached historical data for {symbol}")
                        else:
                            print(f"⚠️ Unexpected cache data type: {type(cached_data)}")
                            data = None
                    except Exception as e:
                        print(f"⚠️ Failed to load cached data: {e}")
                        data = None

            # Fetch fresh data if no valid cache
            if data is None:
                data_type = "LIVE" if is_current_day else "historical"
                print(f"🔴 Fetching {data_type} data for {symbol} ({data_source})")

                data = yf.download(
                    symbol,
                    start=start_date_str,
                    end=end_date_str,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True,
                )
                data = data.reset_index()

                # Only cache historical data (never current-day)
                if not is_current_day:
                    try:
                        # Store as CSV string for efficient caching
                        csv_data = data.to_csv(index=False)
                        success = smart_cache.set_cached_data(
                            cache_key=cache_key,
                            data=csv_data,
                            data_source=data_source,
                            date_str=curr_date_str
                        )
                        if not success:
                            print(f"⚠️ Cache storage was rejected for {symbol}")
                    except Exception as e:
                        print(f"⚠️ Failed to cache data: {e}")
                else:
                    print(f"🔴 Current-day data for {symbol} - NOT caching (time-sensitive)")

            if data is not None and not data.empty:
                df = wrap(data)
                df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            else:
                print(f"⚠️ No data retrieved for {symbol}")
                return "N/A: No data available"

        try:
            # Trigger stockstats to calculate the indicator with error handling
            df[indicator]  # This calculates the indicator

            # Find matching rows for the current date
            matching_rows = df[df["Date"].str.startswith(curr_date)]

            if not matching_rows.empty:
                # Handle potential multiple columns by selecting the first one if needed
                indicator_col = df.columns[df.columns.str.contains(indicator, case=False)]
                if len(indicator_col) > 1:
                    # If multiple columns match, use the exact match or first one
                    exact_match = [col for col in indicator_col if col == indicator]
                    selected_col = exact_match[0] if exact_match else indicator_col[0]
                    print(f"⚠️ Multiple columns found for {indicator}, using: {selected_col}")
                else:
                    selected_col = indicator

                indicator_value = matching_rows[selected_col].values[0]
                return indicator_value
            else:
                return "N/A: Not a trading day (weekend or holiday)"

        except Exception as e:
            print(f"⚠️ StockStats calculation error for {indicator} on {symbol}: {e}")
            # Try fallback calculation or return N/A
            return f"N/A (Error: {str(e)[:50]})"
