"""
Default Configuration Module

This module provides the default configuration for the TradingAgents system.
It integrates with the environment configuration system to load settings from .env files.
"""

from .env_config import get_env_config

# Load environment configuration
env_config = get_env_config()

# Create DEFAULT_CONFIG from environment configuration
DEFAULT_CONFIG = env_config.get_config()

# Export for backward compatibility
def get_default_config():
    """Get the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def update_default_config(updates):
    """Update default configuration with new values."""
    global DEFAULT_CONFIG
    DEFAULT_CONFIG.update(updates)
    env_config.update_config(updates)
