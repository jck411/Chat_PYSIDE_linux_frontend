"""
Configuration Management Package

This package provides a clean separation between:
- Environment variables (API keys, secrets)
- User configuration (backend profiles, UI preferences)
- Runtime configuration management
"""

from .env_config import EnvConfig, get_env_config
from .user_config import UserConfig, get_user_config, ThemePreference
from .backend_profiles import BackendProfile, BackendProfileManager

# Main configuration interface
from .config_manager import ConfigManager, get_config_manager

__all__ = [
    "EnvConfig",
    "UserConfig",
    "BackendProfile",
    "BackendProfileManager",
    "ConfigManager",
    "ThemePreference",
    "get_env_config",
    "get_user_config",
    "get_config_manager",
]
