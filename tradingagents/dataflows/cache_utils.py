"""
Smart Cache Utilities for TradingAgents

Implements intelligent caching with TTL (Time-To-Live) policies to ensure
time-sensitive trading data is always live while allowing appropriate caching
for historical data.
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any, Dict, List
from enum import Enum


class DataType(Enum):
    """Data type classification for cache policies."""
    LIVE = "live"           # No caching - always fetch live
    INTRADAY = "intraday"   # Short TTL caching (5-15 min)
    HISTORICAL = "historical"  # Longer TTL caching (24 hours)
    STATIC = "static"       # Long TTL caching (7 days)


class SmartCache:
    """Smart caching system with TTL and data type classification."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize smart cache with configuration."""
        self.config = config
        self.cache_dir = Path(config.get("data_cache_dir", "./data_cache"))
        self.cache_dir.mkdir(exist_ok=True)

        # Cache policy settings
        self.enabled = config.get("enable_smart_caching", True)
        self.policy = config.get("cache_policy", "smart")

        # TTL settings (in minutes)
        self.ttl_live = config.get("cache_ttl_live_data", 0)
        self.ttl_intraday = config.get("cache_ttl_intraday", 15)
        self.ttl_historical = config.get("cache_ttl_historical", 1440)  # 24 hours
        self.ttl_static = config.get("cache_ttl_static", 10080)  # 7 days

        # Data source classifications
        self.live_sources = set(config.get("live_data_sources", []))
        self.intraday_sources = set(config.get("intraday_data_sources", []))
        self.historical_sources = set(config.get("historical_data_sources", []))

        # Behavior settings
        self.force_live_current_day = config.get("force_live_current_day", True)
        self.bypass_trading_hours = config.get("cache_bypass_trading_hours", True)
        self.max_age_check = config.get("cache_max_age_check", True)

    def classify_data_type(self, data_source: str, date_str: str = None) -> DataType:
        """Classify data type based on source and date."""
        # CRITICAL: Always classify current-day data as LIVE (never cache)
        if date_str:
            try:
                data_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                today = datetime.now().date()
                if data_date == today:
                    return DataType.LIVE
            except (ValueError, TypeError):
                pass

        # Check if it's explicitly a live data source
        if data_source in self.live_sources:
            return DataType.LIVE

        # Current day data sources should always be live
        if "current_day" in data_source.lower():
            return DataType.LIVE

        # Check other classifications
        if data_source in self.intraday_sources:
            return DataType.INTRADAY
        elif data_source in self.historical_sources:
            return DataType.HISTORICAL
        else:
            # Default to static for unclassified sources
            return DataType.STATIC

    def get_ttl_minutes(self, data_type: DataType) -> int:
        """Get TTL in minutes for a data type."""
        ttl_map = {
            DataType.LIVE: self.ttl_live,
            DataType.INTRADAY: self.ttl_intraday,
            DataType.HISTORICAL: self.ttl_historical,
            DataType.STATIC: self.ttl_static,
        }
        return ttl_map.get(data_type, 0)

    def _get_cache_path(self, cache_key: str, data_format: str = "cache") -> Path:
        """Generate cache file path with appropriate extension."""
        return self.cache_dir / f"{cache_key}.{data_format}"

    def _get_metadata_path(self, cache_key: str) -> Path:
        """Generate cache metadata file path."""
        return self.cache_dir / f"{cache_key}.meta"

    def _is_cache_valid(self, cache_key: str, ttl_minutes: int) -> bool:
        """Check if cache is valid based on TTL."""
        metadata_path = self._get_metadata_path(cache_key)

        # Check if metadata exists
        if not metadata_path.exists():
            return False

        # Check if any cache file exists
        cache_exists = False
        for ext in ['csv', 'json', 'cache']:
            if self._get_cache_path(cache_key, ext).exists():
                cache_exists = True
                break

        if not cache_exists:
            return False

        if not self.max_age_check:
            return True

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            cache_time = datetime.fromisoformat(metadata['timestamp'])
            age_minutes = (datetime.now() - cache_time).total_seconds() / 60

            is_valid = age_minutes < ttl_minutes
            if not is_valid:
                print(f"🕐 Cache expired for {cache_key} (age: {age_minutes:.1f} min, TTL: {ttl_minutes} min)")

            return is_valid
        except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️ Cache validation failed for {cache_key}: {e}")
            return False

    def should_use_cache(self, data_source: str, date_str: str = None, cache_key: str = None) -> bool:
        """Determine if cache should be used for this request."""
        if not self.enabled or self.policy == "disabled":
            return False

        # CRITICAL: Never cache current-day or time-sensitive data
        if date_str:
            try:
                data_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                today = datetime.now().date()
                if data_date == today:
                    print(f"🔴 Current-day data detected - forcing live fetch for {data_source}")
                    return False
            except (ValueError, TypeError):
                pass

        # Never cache live data
        data_type = self.classify_data_type(data_source, date_str)
        if data_type == DataType.LIVE:
            print(f"🔴 Live data type detected - forcing live fetch for {data_source}")
            return False

        # Check trading hours bypass (during market hours, prefer live data)
        if self.bypass_trading_hours and self._is_trading_hours():
            if data_type in [DataType.INTRADAY, DataType.LIVE]:
                print(f"🔴 Trading hours bypass - forcing live fetch for {data_source}")
                return False

        # Check cache validity if cache key provided
        if cache_key:
            ttl_minutes = self.get_ttl_minutes(data_type)
            return self._is_cache_valid(cache_key, ttl_minutes)

        return True

    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from cache if valid."""
        # Try different file formats
        for ext, is_text in [('csv', True), ('json', True), ('cache', False)]:
            cache_path = self._get_cache_path(cache_key, ext)
            if cache_path.exists():
                try:
                    if is_text:
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            if ext == 'json':
                                return json.load(f)
                            else:  # CSV
                                return f.read()
                    else:
                        with open(cache_path, 'rb') as f:
                            return f.read()
                except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"⚠️ Failed to load cached data from {cache_path}: {e}")
                    continue
        return None

    def set_cached_data(self, cache_key: str, data: Any, data_source: str, date_str: str = None) -> bool:
        """Store data in cache with metadata."""
        if not self.enabled:
            return False

        data_type = self.classify_data_type(data_source, date_str)

        # Never cache live data
        if data_type == DataType.LIVE:
            print(f"🔴 Refusing to cache LIVE data: {data_source}")
            return False

        try:
            # Determine file format and store data
            if isinstance(data, (dict, list)):
                cache_path = self._get_cache_path(cache_key, "json")
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            elif isinstance(data, str):
                # Assume CSV format for string data
                cache_path = self._get_cache_path(cache_key, "csv")
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            else:
                # Binary data
                cache_path = self._get_cache_path(cache_key, "cache")
                with open(cache_path, 'wb') as f:
                    f.write(data)

            # Store metadata
            metadata_path = self._get_metadata_path(cache_key)
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'data_type': data_type.value,
                'data_source': data_source,
                'date_str': date_str,
                'ttl_minutes': self.get_ttl_minutes(data_type),
                'file_format': cache_path.suffix[1:]  # Remove the dot
            }

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            print(f"💾 Cached {data_type.value} data: {cache_key} ({cache_path.suffix})")
            return True

        except (OSError, TypeError) as e:
            print(f"⚠️ Failed to cache data for {cache_key}: {e}")
            return False

    def invalidate_cache(self, cache_key: str) -> bool:
        """Invalidate specific cache entry."""
        metadata_path = self._get_metadata_path(cache_key)

        removed = False
        # Remove all possible cache file formats
        for ext in ['csv', 'json', 'cache']:
            cache_path = self._get_cache_path(cache_key, ext)
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    removed = True
                except OSError:
                    pass

        # Remove metadata
        if metadata_path.exists():
            try:
                metadata_path.unlink()
                removed = True
            except OSError:
                pass

        return removed

    def clean_expired_cache(self) -> int:
        """Clean all expired cache entries. Returns number of entries removed."""
        removed_count = 0

        for metadata_file in self.cache_dir.glob("*.meta"):
            cache_key = metadata_file.stem

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Check if cache is expired
                cache_time = datetime.fromisoformat(metadata['timestamp'])
                ttl_minutes = metadata.get('ttl_minutes', 0)
                age_minutes = (datetime.now() - cache_time).total_seconds() / 60

                if age_minutes >= ttl_minutes:
                    # Remove expired cache (all possible formats)
                    for ext in ['csv', 'json', 'cache']:
                        cache_path = self._get_cache_path(cache_key, ext)
                        if cache_path.exists():
                            cache_path.unlink()

                    # Remove metadata
                    metadata_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                # Remove corrupted cache files
                for ext in ['csv', 'json', 'cache']:
                    cache_path = self._get_cache_path(cache_key, ext)
                    if cache_path.exists():
                        try:
                            cache_path.unlink()
                        except OSError:
                            pass

                # Remove corrupted metadata
                if metadata_file.exists():
                    try:
                        metadata_file.unlink()
                        removed_count += 1
                    except OSError:
                        pass

        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'total_entries': 0,
            'by_type': {dt.value: 0 for dt in DataType},
            'expired_entries': 0,
            'cache_size_mb': 0
        }

        total_size = 0
        for metadata_file in self.cache_dir.glob("*.meta"):
            cache_key = metadata_file.stem

            # Calculate size from all possible cache file formats
            for ext in ['csv', 'json', 'cache']:
                cache_path = self._get_cache_path(cache_key, ext)
                if cache_path.exists():
                    total_size += cache_path.stat().st_size

            total_size += metadata_file.stat().st_size

            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                stats['total_entries'] += 1
                data_type = metadata.get('data_type', 'unknown')
                if data_type in stats['by_type']:
                    stats['by_type'][data_type] += 1

                # Check if expired
                cache_time = datetime.fromisoformat(metadata['timestamp'])
                ttl_minutes = metadata.get('ttl_minutes', 0)
                age_minutes = (datetime.now() - cache_time).total_seconds() / 60

                if age_minutes >= ttl_minutes:
                    stats['expired_entries'] += 1

            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        stats['cache_size_mb'] = round(total_size / (1024 * 1024), 2)
        return stats

    def _is_trading_hours(self) -> bool:
        """Check if current time is during trading hours (9:30 AM - 4:00 PM EST)."""
        try:
            from datetime import timezone, timedelta

            # Convert to EST
            est = timezone(timedelta(hours=-5))  # Simplified - doesn't handle DST
            now_est = datetime.now(est)

            # Check if weekday and within trading hours
            if now_est.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False

            trading_start = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
            trading_end = now_est.replace(hour=16, minute=0, second=0, microsecond=0)

            return trading_start <= now_est <= trading_end
        except:
            # If timezone calculation fails, assume it's trading hours to be safe
            return True


def create_cache_key(data_source: str, symbol: str = None, start_date: str = None,
                     end_date: str = None, **kwargs) -> str:
    """Create a standardized cache key."""
    parts = [data_source]

    if symbol:
        parts.append(symbol)
    if start_date:
        parts.append(start_date)
    if end_date:
        parts.append(end_date)

    # Add other parameters
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}:{value}")

    return "_".join(parts)


# Global cache instance
_smart_cache = None

def get_smart_cache():
    """Get global smart cache instance."""
    global _smart_cache
    if _smart_cache is None:
        from ..default_config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG
        _smart_cache = SmartCache(config)
    return _smart_cache