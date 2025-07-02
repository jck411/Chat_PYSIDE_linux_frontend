"""
Theme System Package

Following PROJECT_RULES.md:
- Clean package interface
- Minimal public API
- Type-safe exports
"""

from .theme_config import ThemeMode, ThemeConfig, LIGHT_THEME, DARK_THEME
from .theme_manager import ThemeManager, get_theme_manager
from .theme_applier import ThemeApplier
from .icon_button import MaterialIconButton

# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "ThemeMode",
    "ThemeConfig",
    "LIGHT_THEME",
    "DARK_THEME",
    "ThemeManager",
    "get_theme_manager",
    "ThemeApplier",
    "MaterialIconButton",
]
