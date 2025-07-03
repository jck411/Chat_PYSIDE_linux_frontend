"""
Theme Configuration with Material Design Colors

Following PROJECT_RULES.md:
- Structured theme definitions
- Material Design 3 color system
- Type-safe configuration
- Extensible design
"""

from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    """Available theme modes"""

    LIGHT = "light"
    DARK = "dark"


@dataclass
class ColorPalette:
    """Material Design 3 color palette"""

    # Primary colors
    primary: str
    on_primary: str
    primary_container: str
    on_primary_container: str

    # Secondary colors
    secondary: str
    on_secondary: str
    secondary_container: str
    on_secondary_container: str

    # Surface colors
    surface: str
    on_surface: str
    surface_variant: str
    on_surface_variant: str

    # Background colors
    background: str
    on_background: str

    # Error colors
    error: str
    on_error: str
    error_container: str
    on_error_container: str

    # Outline colors
    outline: str
    outline_variant: str

    # Shadow and scrim
    shadow: str
    scrim: str


@dataclass
class ThemeConfig:
    """Complete theme configuration"""

    name: str
    mode: ThemeMode
    colors: ColorPalette

    # UI specific colors
    chat_background: str
    user_message_bg: str
    assistant_message_bg: str
    input_background: str
    button_background: str
    button_hover: str
    status_connected: str
    status_disconnected: str
    status_connecting: str


# Material Design 3 Light Theme
LIGHT_COLORS = ColorPalette(
    # Primary colors - Blue
    primary="#1976D2",
    on_primary="#FFFFFF",
    primary_container="#BBDEFB",
    on_primary_container="#0D47A1",
    # Secondary colors - Teal
    secondary="#00796B",
    on_secondary="#FFFFFF",
    secondary_container="#B2DFDB",
    on_secondary_container="#004D40",
    # Surface colors
    surface="#FFFFFF",
    on_surface="#1C1B1F",
    surface_variant="#F3F3F3",
    on_surface_variant="#49454F",
    # Background colors
    background="#FEFBFF",
    on_background="#1C1B1F",
    # Error colors
    error="#D32F2F",
    on_error="#FFFFFF",
    error_container="#FFCDD2",
    on_error_container="#B71C1C",
    # Outline colors
    outline="#79747E",
    outline_variant="#CAC4D0",
    # Shadow and scrim
    shadow="#000000",
    scrim="#000000",
)

# Material Design 3 Dark Theme
DARK_COLORS = ColorPalette(
    # Primary colors - Blue
    primary="#90CAF9",
    on_primary="#0D47A1",
    primary_container="#1565C0",
    on_primary_container="#E3F2FD",
    # Secondary colors - Teal
    secondary="#4DB6AC",
    on_secondary="#004D40",
    secondary_container="#00695C",
    on_secondary_container="#E0F2F1",
    # Surface colors
    surface="#121212",
    on_surface="#E6E1E5",
    surface_variant="#1E1E1E",
    on_surface_variant="#CAC4D0",
    # Background colors
    background="#0F0F0F",
    on_background="#E6E1E5",
    # Error colors
    error="#EF5350",
    on_error="#B71C1C",
    error_container="#D32F2F",
    on_error_container="#FFCDD2",
    # Outline colors
    outline="#938F99",
    outline_variant="#49454F",
    # Shadow and scrim
    shadow="#000000",
    scrim="#000000",
)

# Light theme configuration
LIGHT_THEME = ThemeConfig(
    name="Light",
    mode=ThemeMode.LIGHT,
    colors=LIGHT_COLORS,
    # UI specific colors
    chat_background="#FFFFFF",
    user_message_bg="#E3F2FD",
    assistant_message_bg="#F5F5F5",
    input_background="#FFFFFF",
    button_background="#1976D2",
    button_hover="#1565C0",
    status_connected="#4CAF50",
    status_disconnected="#F44336",
    status_connecting="#FF9800",
)

# Dark theme configuration
DARK_THEME = ThemeConfig(
    name="Dark",
    mode=ThemeMode.DARK,
    colors=DARK_COLORS,
    # UI specific colors
    chat_background="#1E1E1E",
    user_message_bg="#263238",
    assistant_message_bg="#2E2E2E",
    input_background="#2E2E2E",
    button_background="#90CAF9",
    button_hover="#64B5F6",
    status_connected="#66BB6A",
    status_disconnected="#EF5350",
    status_connecting="#FFA726",
)

# Available themes registry
AVAILABLE_THEMES: dict[ThemeMode, ThemeConfig] = {
    ThemeMode.LIGHT: LIGHT_THEME,
    ThemeMode.DARK: DARK_THEME,
}


def get_theme_config(mode: ThemeMode) -> ThemeConfig:
    """Get theme configuration for specified mode"""
    return AVAILABLE_THEMES[mode]


def get_available_theme_modes() -> list[ThemeMode]:
    """Get list of available theme modes"""
    return list(AVAILABLE_THEMES.keys())


# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "ColorPalette",
    "ThemeConfig",
    "ThemeMode",
    "get_available_theme_modes",
    "get_theme_config",
]
