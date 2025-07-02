"""
Configuration Manager

Main configuration interface that coordinates environment, user, and backend configurations.
Following PROJECT_RULES.md:
- Single responsibility
- Fail-fast validation
- Structured logging
"""

import structlog
from typing import Optional, Dict, Any
from pathlib import Path

from .env_config import get_env_config
from .user_config import get_user_config, ThemePreference
from .backend_profiles import BackendProfile, BackendProfileManager


class ConfigManager:
    """
    Main configuration manager that coordinates all configuration sources.

    Provides a unified interface for accessing environment variables,
    user preferences, and backend profiles.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.logger = structlog.get_logger(__name__)

        # Initialize configuration components
        self.env_config = get_env_config()
        self.user_config = get_user_config(config_path)
        self.backend_manager = BackendProfileManager()

        # Load backend profiles from user config if available
        self._load_backend_profiles()

        self.logger.info(
            "Configuration manager initialized",
            config_event="config_manager_init",
            module=__name__,
            env_services=self.env_config.get_configured_services(),
            active_backend=self.backend_manager.get_active_profile_id(),
            theme=self.user_config.get_theme_preference().value,
        )

    def _load_backend_profiles(self) -> None:
        """Load backend profiles from user configuration"""
        try:
            backend_data = self.user_config.ui_config.backend_profiles
            if backend_data:
                self.backend_manager.from_dict(backend_data)
                self.logger.info(
                    "Backend profiles loaded from user config",
                    config_event="backend_profiles_loaded",
                    module=__name__,
                    profile_count=len(self.backend_manager.list_profiles()),
                )
        except Exception as e:
            self.logger.error(
                "Failed to load backend profiles from user config",
                config_event="backend_profiles_load_failed",
                module=__name__,
                error=str(e),
            )

    def _save_backend_profiles(self) -> None:
        """Save backend profiles to user configuration"""
        try:
            backend_data = self.backend_manager.to_dict()
            self.user_config.ui_config.backend_profiles = backend_data
            self.user_config.save()
            self.logger.info(
                "Backend profiles saved to user config",
                config_event="backend_profiles_saved",
                module=__name__,
                profile_count=len(self.backend_manager.list_profiles()),
            )
        except Exception as e:
            self.logger.error(
                "Failed to save backend profiles to user config",
                config_event="backend_profiles_save_failed",
                module=__name__,
                error=str(e),
            )

    # Environment Configuration Methods
    def get_speechgram_api_key(self) -> Optional[str]:
        """Get Speechgram API key from environment"""
        return self.env_config.get_speechgram_api_key()

    def has_speechgram_api_key(self) -> bool:
        """Check if Speechgram API key is available"""
        return self.env_config.has_speechgram_api_key()

    # User Configuration Methods
    def get_theme_preference(self) -> ThemePreference:
        """Get current theme preference"""
        return self.user_config.get_theme_preference()

    def set_theme_preference(self, theme: ThemePreference) -> None:
        """Set theme preference"""
        self.user_config.set_theme_preference(theme)

        self.logger.info(
            "Theme preference changed via config manager",
            config_event="theme_changed",
            module=__name__,
            theme=theme.value,
        )

    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry as dictionary"""
        geometry = self.user_config.get_window_geometry()
        return {
            "width": geometry.width,
            "height": geometry.height,
            "x": geometry.x,
            "y": geometry.y,
        }

    def set_window_geometry(self, width: int, height: int, x: int, y: int) -> None:
        """Set window geometry"""
        from .user_config import WindowGeometry

        geometry = WindowGeometry(width=width, height=height, x=x, y=y)
        self.user_config.set_window_geometry(geometry)

    # Backend Configuration Methods
    def get_active_backend_profile(self) -> Optional[BackendProfile]:
        """Get the currently active backend profile"""
        return self.backend_manager.get_active_profile()

    def get_active_backend_id(self) -> Optional[str]:
        """Get the currently active backend profile ID"""
        return self.backend_manager.get_active_profile_id()

    def set_active_backend(self, profile_id: str) -> None:
        """Set the active backend profile"""
        self.backend_manager.set_active_profile(profile_id)
        self._save_backend_profiles()

        self.logger.info(
            "Active backend changed via config manager",
            config_event="backend_changed",
            module=__name__,
            profile_id=profile_id,
        )

    def add_backend_profile(
        self,
        profile_id: str,
        name: str,
        host: str,
        port: int,
        use_ssl: bool,
        description: Optional[str] = None,
    ) -> None:
        """Add a new backend profile"""
        profile = BackendProfile(
            name=name, host=host, port=port, use_ssl=use_ssl, description=description
        )
        self.backend_manager.add_profile(profile_id, profile)
        self._save_backend_profiles()

    def remove_backend_profile(self, profile_id: str) -> None:
        """Remove a backend profile"""
        self.backend_manager.remove_profile(profile_id)
        self._save_backend_profiles()

    def update_backend_profile(
        self,
        profile_id: str,
        name: str,
        host: str,
        port: int,
        use_ssl: bool,
        description: Optional[str] = None,
    ) -> None:
        """Update an existing backend profile"""
        profile = BackendProfile(
            name=name, host=host, port=port, use_ssl=use_ssl, description=description
        )
        self.backend_manager.update_profile(profile_id, profile)
        self._save_backend_profiles()

    def list_backend_profiles(self) -> Dict[str, str]:
        """Get mapping of profile IDs to names"""
        return self.backend_manager.list_profile_names()

    def get_backend_profile(self, profile_id: str) -> Optional[BackendProfile]:
        """Get a specific backend profile"""
        return self.backend_manager.get_profile(profile_id)

    # Convenience Methods for Current Backend
    def get_websocket_url(self) -> Optional[str]:
        """Get WebSocket URL for active backend"""
        profile = self.get_active_backend_profile()
        return profile.websocket_url if profile else None

    def get_health_url(self) -> Optional[str]:
        """Get health check URL for active backend"""
        profile = self.get_active_backend_profile()
        return profile.health_url if profile else None

    def get_base_url(self) -> Optional[str]:
        """Get base URL for active backend"""
        profile = self.get_active_backend_profile()
        return profile.base_url if profile else None

    # Validation and Status Methods
    def validate_all(self, require_speechgram: bool = False) -> Dict[str, Any]:
        """
        Validate all configuration components.

        Args:
            require_speechgram: Whether to require Speechgram API key

        Returns:
            Dictionary with comprehensive validation results
        """
        validation_results: Dict[str, Any] = {
            "status": "valid",
            "components": {},
            "issues": [],
            "recommendations": [],
        }

        try:
            # Validate environment configuration
            from .env_config import validate_environment

            env_validation = validate_environment(require_speechgram=require_speechgram)
            validation_results["components"]["environment"] = env_validation

            if env_validation["status"] != "valid":
                validation_results["issues"].extend(env_validation["issues"])
                validation_results["recommendations"].extend(
                    env_validation["recommendations"]
                )

            # Validate user configuration
            user_validation = self.user_config.validate()
            validation_results["components"]["user_config"] = user_validation

            if user_validation["status"] != "valid":
                validation_results["issues"].extend(user_validation["issues"])
                validation_results["recommendations"].extend(
                    user_validation["recommendations"]
                )

            # Validate backend configuration
            active_profile = self.get_active_backend_profile()
            if active_profile:
                validation_results["components"]["backend"] = {
                    "status": "valid",
                    "active_profile": str(active_profile),
                }
            else:
                validation_results["issues"].append("No active backend profile")
                validation_results["components"]["backend"] = {"status": "invalid"}

            # Set overall status
            if validation_results["issues"]:
                validation_results["status"] = "invalid"

            self.logger.info(
                "Configuration validation completed",
                config_event="validation_completed",
                module=__name__,
                status=validation_results["status"],
                issue_count=len(validation_results["issues"]),
            )

        except Exception as e:
            validation_results["status"] = "error"
            validation_results["issues"].append(f"Validation error: {str(e)}")

            self.logger.error(
                "Configuration validation failed",
                config_event="validation_failed",
                module=__name__,
                error=str(e),
            )

        return validation_results

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration status"""
        active_profile = self.get_active_backend_profile()

        return {
            "environment": {
                "speechgram_configured": self.has_speechgram_api_key(),
                "configured_services": self.env_config.get_configured_services(),
            },
            "user_config": self.user_config.get_config_info(),
            "backend": {
                "active_profile_id": self.get_active_backend_id(),
                "active_profile_name": active_profile.name if active_profile else None,
                "websocket_url": self.get_websocket_url(),
                "total_profiles": len(self.backend_manager.list_profiles()),
            },
            "theme": self.get_theme_preference().value,
        }

    def reset_user_config(self) -> None:
        """Reset user configuration to defaults"""
        self.user_config.reset_to_defaults()

        self.logger.info(
            "User configuration reset via config manager",
            config_event="user_config_reset",
            module=__name__,
        )


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Path] = None) -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "ConfigManager",
    "get_config_manager",
]
