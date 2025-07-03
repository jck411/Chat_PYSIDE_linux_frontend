"""
Central Theme Manager with Signal-Based Updates

Following PROJECT_RULES.md:
- Singleton pattern for global theme state
- Qt signals for real-time updates
- QSettings integration for persistence
- Under 10ms theme switching performance
"""

import os
from typing import Optional

import structlog
from PySide6.QtCore import QObject, QSettings, Signal

from .theme_applier import ThemeApplier
from .theme_config import ThemeConfig, ThemeMode, get_theme_config


class ThemeManager(QObject):
    """
    Central theme management with persistence and real-time updates.

    Features:
    - Singleton pattern for global access
    - Signal-based theme change notifications
    - QSettings persistence
    - Environment variable support
    - Performance-optimized switching
    """

    # Signals for theme changes
    theme_changed = Signal(ThemeConfig)
    theme_mode_changed = Signal(ThemeMode)

    _instance: Optional["ThemeManager"] = None

    def __new__(cls) -> "ThemeManager":
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        super().__init__()
        self.logger = structlog.get_logger(__name__)

        # Initialize components
        self._theme_applier = ThemeApplier()
        self._settings = QSettings("ChatPySideFrontend", "ThemeSettings")

        # Current theme state
        self._current_mode: ThemeMode = self._load_theme_preference()
        self._current_config: ThemeConfig = get_theme_config(self._current_mode)

        # Mark as initialized
        self._initialized = True

        self.logger.info(
            "Theme manager initialized",
            theme_event="manager_init",
            module=__name__,
            initial_theme=self._current_mode.value,
        )

    @property
    def current_mode(self) -> ThemeMode:
        """Get current theme mode"""
        return self._current_mode

    @property
    def current_config(self) -> ThemeConfig:
        """Get current theme configuration"""
        return self._current_config

    def set_theme_mode(self, mode: ThemeMode) -> None:
        """
        Set theme mode with immediate application and persistence.

        Args:
            mode: Theme mode to apply
        """
        if mode == self._current_mode:
            return  # No change needed

        self.logger.info(
            "Changing theme mode",
            theme_event="theme_change_start",
            module=__name__,
            from_theme=self._current_mode.value,
            to_theme=mode.value,
        )

        # Update internal state
        self._current_mode = mode
        self._current_config = get_theme_config(mode)

        # Apply theme immediately
        self._theme_applier.apply_theme_to_application(self._current_config)

        # Persist preference
        self._save_theme_preference(mode)

        # Emit signals for other components
        self.theme_mode_changed.emit(mode)
        self.theme_changed.emit(self._current_config)

        self.logger.info(
            "Theme mode changed successfully",
            theme_event="theme_change_complete",
            module=__name__,
            new_theme=mode.value,
        )

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes"""
        new_mode = (
            ThemeMode.DARK if self._current_mode == ThemeMode.LIGHT else ThemeMode.LIGHT
        )
        self.set_theme_mode(new_mode)

    def apply_current_theme(self) -> None:
        """Apply current theme to application (useful for initialization)"""
        self._theme_applier.apply_theme_to_application(self._current_config)

        self.logger.info(
            "Current theme applied",
            theme_event="theme_applied",
            module=__name__,
            theme_mode=self._current_mode.value,
        )

    def _load_theme_preference(self) -> ThemeMode:
        """Load theme preference from environment or settings"""
        # Check environment variable first (per PROJECT_RULES.md)
        env_theme = os.getenv("CHAT_THEME_MODE", "").lower()
        if env_theme in ["light", "dark"]:
            try:
                return ThemeMode(env_theme)
            except ValueError:
                pass

        # Fall back to QSettings
        saved_theme = self._settings.value("theme_mode", ThemeMode.LIGHT.value)
        try:
            return ThemeMode(saved_theme)
        except ValueError:
            # Invalid saved value, default to light
            self.logger.warning(
                "Invalid saved theme mode, defaulting to light",
                theme_event="invalid_saved_theme",
                module=__name__,
                saved_value=saved_theme,
            )
            return ThemeMode.LIGHT

    def _save_theme_preference(self, mode: ThemeMode) -> None:
        """Save theme preference to QSettings"""
        self._settings.setValue("theme_mode", mode.value)
        self._settings.sync()

        self.logger.debug(
            "Theme preference saved",
            theme_event="preference_saved",
            module=__name__,
            theme_mode=mode.value,
        )

    def get_theme_info(self) -> dict:
        """Get current theme information for debugging/logging"""
        return {
            "mode": self._current_mode.value,
            "name": self._current_config.name,
            "primary_color": self._current_config.colors.primary,
            "background_color": self._current_config.colors.background,
        }

    def clear_cache(self) -> None:
        """Clear theme cache and force regeneration"""
        self._theme_applier.clear_cache()
        self.logger.info(
            "Theme cache cleared", theme_event="cache_cleared", module=__name__
        )


# Global theme manager instance
def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance"""
    return ThemeManager()


# Export only necessary symbols per PROJECT_RULES.md
__all__ = ["ThemeManager", "get_theme_manager"]
