"""
Theme System Package

Following PROJECT_RULES.md:
- Clean package interface
- Minimal public API
- Type-safe exports
"""

from .font_manager import FontManager, get_font_manager
from .icon_button import MaterialIconButton
from .theme_applier import ThemeApplier
from .theme_config import DARK_THEME, LIGHT_THEME, ThemeConfig, ThemeMode
from .theme_manager import ThemeManager, get_theme_manager

# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "FontManager",
    "MaterialIconButton",
    "ThemeApplier",
    "ThemeConfig",
    "ThemeManager",
    "ThemeMode",
    "get_font_manager",
    "get_theme_manager",
]
