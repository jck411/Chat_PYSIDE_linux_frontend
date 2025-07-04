"""
Theme System Package

Following PROJECT_RULES.md:
- Clean package interface
- Minimal public API
- Type-safe exports
"""

from .icon_button import MaterialIconButton
from .theme_applier import ThemeApplier
from .theme_config import DARK_THEME, LIGHT_THEME, ThemeConfig, ThemeMode
from .theme_manager import ThemeManager, get_theme_manager

# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "MaterialIconButton",
    "ThemeApplier",
    "ThemeConfig",
    "ThemeManager",
    "ThemeMode",
    "get_theme_manager",
]
