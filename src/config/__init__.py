"""
Configuration Management Package

This package provides a clean separation between:
- Environment variables (API keys, secrets)
- User configuration (backend profiles, UI preferences)
- Runtime configuration management
"""

from .backend_profiles import BackendProfile, BackendProfileManager

# Main configuration interface
from .config_manager import ConfigManager, get_config_manager
from .env_config import EnvConfig, get_env_config
from .user_config import ThemePreference, UserConfig, get_user_config

__all__ = [
    "BackendProfile",
    "BackendProfileManager",
    "ConfigManager",
    "EnvConfig",
    "ThemePreference",
    "UserConfig",
    "get_config_manager",
    "get_env_config",
    "get_user_config",
]
