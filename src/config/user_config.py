"""
User Configuration Management

Handles user preferences and settings stored in JSON format.
Following PROJECT_RULES.md:
- Fail-fast validation
- Structured logging
"""

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import structlog


class ThemePreference(Enum):
    """Theme preference options"""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"  # Future: follow system theme


@dataclass
class WindowGeometry:
    """Window geometry configuration"""

    width: int = 800
    height: int = 600
    x: int = 100
    y: int = 100

    def __post_init__(self) -> None:
        """Validate geometry values"""
        if self.width < 400 or self.height < 300:
            raise ValueError("Window size too small (minimum 400x300)")
        if self.x < 0 or self.y < 0:
            raise ValueError("Window position cannot be negative")


@dataclass
class UIConfig:
    """UI configuration settings"""

    theme: ThemePreference = ThemePreference.LIGHT
    window_geometry: WindowGeometry = field(default_factory=WindowGeometry)
    backend_profiles: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "theme": self.theme.value,
            "window_geometry": asdict(self.window_geometry),
            "backend_profiles": self.backend_profiles,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UIConfig":
        """Create from dictionary (JSON deserialization)"""
        theme_str = data.get("theme", "light")
        try:
            theme = ThemePreference(theme_str)
        except ValueError:
            theme = ThemePreference.LIGHT

        geometry_data = data.get("window_geometry", {})
        geometry = WindowGeometry(**geometry_data)

        backend_profiles = data.get("backend_profiles", {})

        return cls(
            theme=theme, window_geometry=geometry, backend_profiles=backend_profiles
        )


class UserConfig:
    """
    User configuration management with JSON persistence.

    Handles loading, saving, and managing user preferences including
    UI settings, backend profiles, and other user-specific configuration.
    """

    CONFIG_VERSION = "1.0"
    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "chat-frontend"
    DEFAULT_CONFIG_FILE = "config.json"

    def __init__(self, config_path: Path | None = None):
        self.logger = structlog.get_logger(__name__)

        # Determine config file path
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = self.DEFAULT_CONFIG_DIR / self.DEFAULT_CONFIG_FILE

        # Initialize configuration
        self.ui_config = UIConfig()
        self._version = self.CONFIG_VERSION

        # Load existing configuration
        self.load()

        self.logger.info(
            "User configuration initialized",
            config_event="user_config_init",
            module=__name__,
            config_path=str(self.config_path),
            version=self._version,
        )

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """
        Load configuration from JSON file.

        Creates default configuration if file doesn't exist.
        """
        try:
            if not self.config_path.exists():
                self.logger.info(
                    "Configuration file not found, using defaults",
                    config_event="config_file_not_found",
                    module=__name__,
                    config_path=str(self.config_path),
                )
                return

            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            # Load version
            self._version = data.get("version", "1.0")

            # Load UI configuration
            ui_data = data.get("ui", {})
            self.ui_config = UIConfig.from_dict(ui_data)

            self.logger.info(
                "User configuration loaded",
                config_event="config_loaded",
                module=__name__,
                config_path=str(self.config_path),
                version=self._version,
            )

        except Exception as e:
            self.logger.error(
                "Failed to load user configuration",
                config_event="config_load_failed",
                module=__name__,
                config_path=str(self.config_path),
                error=str(e),
            )
            # Continue with defaults

    def save(self) -> None:
        """
        Save configuration to JSON file.

        Raises:
            IOError: If unable to write configuration file
        """
        try:
            self._ensure_config_dir()

            config_data = {
                "version": self._version,
                "ui": self.ui_config.to_dict(),
            }

            # Write atomically using temporary file
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.config_path)

            self.logger.info(
                "User configuration saved",
                config_event="config_saved",
                module=__name__,
                config_path=str(self.config_path),
            )

        except Exception as e:
            self.logger.error(
                "Failed to save user configuration",
                config_event="config_save_failed",
                module=__name__,
                config_path=str(self.config_path),
                error=str(e),
            )
            raise OSError(f"Failed to save configuration: {e}") from e

    def get_theme_preference(self) -> ThemePreference:
        """Get current theme preference"""
        return self.ui_config.theme

    def set_theme_preference(self, theme: ThemePreference) -> None:
        """Set theme preference and save configuration"""
        self.ui_config.theme = theme
        self.save()

        self.logger.info(
            "Theme preference updated",
            config_event="theme_updated",
            module=__name__,
            theme=theme.value,
        )

    def get_window_geometry(self) -> WindowGeometry:
        """Get window geometry configuration"""
        return self.ui_config.window_geometry

    def set_window_geometry(self, geometry: WindowGeometry) -> None:
        """Set window geometry and save configuration"""
        self.ui_config.window_geometry = geometry
        self.save()

        self.logger.info(
            "Window geometry updated",
            config_event="geometry_updated",
            module=__name__,
            geometry=asdict(geometry),
        )

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.ui_config = UIConfig()
        self.save()

        self.logger.info(
            "Configuration reset to defaults",
            config_event="config_reset",
            module=__name__,
        )

    def get_config_info(self) -> dict[str, Any]:
        """Get configuration information for debugging"""
        return {
            "version": self._version,
            "config_path": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "theme": self.ui_config.theme.value,
            "window_geometry": asdict(self.ui_config.window_geometry),
        }

    def validate(self) -> dict[str, Any]:
        """
        Validate current configuration.

        Returns:
            Dictionary with validation results
        """
        validation_results: dict[str, Any] = {
            "status": "valid",
            "issues": [],
            "recommendations": [],
        }

        try:
            # Validate UI config
            if self.ui_config.window_geometry.width < 400:
                validation_results["issues"].append("Window width too small")

            if self.ui_config.window_geometry.height < 300:
                validation_results["issues"].append("Window height too small")

            # Check if config directory is writable
            if not self.config_path.parent.exists():
                validation_results["recommendations"].append(
                    f"Configuration directory will be created: {self.config_path.parent}"
                )

            if validation_results["issues"]:
                validation_results["status"] = "invalid"

        except Exception as e:
            validation_results["status"] = "invalid"
            validation_results["issues"].append(str(e))

        return validation_results


# Global instance
_user_config: UserConfig | None = None


def get_user_config(config_path: Path | None = None) -> UserConfig:
    """Get the global user configuration instance"""
    global _user_config
    if _user_config is None:
        # Check for environment override
        from .env_config import get_env_config

        env_config = get_env_config()
        override_path = env_config.get_config_path_override()

        _user_config = UserConfig(config_path=config_path or override_path)
    return _user_config


# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "ThemePreference",
    "UIConfig",
    "UserConfig",
    "WindowGeometry",
    "get_user_config",
]
