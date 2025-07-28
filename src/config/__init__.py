"""
Configuration Management Package

This package provides a clean separation between:
- Environment variables (API keys, secrets)
- User configuration (backend profiles, UI preferences)
- Runtime configuration management
- Provider-specific optimizations
"""

from .backend_profiles import BackendProfile, BackendProfileManager

# Main configuration interface
from .config_manager import ConfigManager, get_config_manager
from .env_config import EnvConfig, get_env_config
from .provider_config import ProviderConfigManager, ProviderOptimizations, ProviderType
from .user_config import ThemePreference, UserConfig, get_user_config

__all__ = [
    "BackendProfile",
    "BackendProfileManager",
    "ConfigManager",
    "EnvConfig",
    "ProviderConfigManager",
    "ProviderOptimizations",
    "ProviderType",
    "ThemePreference",
    "UserConfig",
    "get_config_manager",
    "get_env_config",
    "get_user_config",
]
