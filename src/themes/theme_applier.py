"""
Theme Applier for Dynamic Widget Styling

Following PROJECT_RULES.md:
- Performance-optimized updates
- Widget-specific styling logic
- Cached stylesheet generation
- Under 10ms theme switching
"""

import structlog
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from .theme_config import ThemeConfig, ThemeMode


class ThemeApplier(QObject):
    """
    Applies themes to widgets with performance optimization.

    Features:
    - Cached stylesheet generation
    - Widget-specific styling
    - Minimal UI thread impact
    - Resource-efficient updates
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = structlog.get_logger(__name__)
        self._stylesheet_cache: dict[ThemeMode, str] = {}

    def apply_theme_to_application(self, theme_config: ThemeConfig) -> None:
        """Apply theme to entire application"""
        self.logger.info(
            "Applying theme to application",
            theme_event="theme_apply_start",
            module=__name__,
            theme_name=theme_config.name,
            theme_mode=theme_config.mode.value,
        )

        # Get or generate stylesheet
        stylesheet = self._get_application_stylesheet(theme_config)

        # Apply to application
        app = QApplication.instance()
        if app and isinstance(app, QApplication):
            app.setStyleSheet(stylesheet)

        self.logger.info(
            "Theme applied successfully",
            theme_event="theme_apply_complete",
            module=__name__,
            theme_name=theme_config.name,
            stylesheet_length=len(stylesheet),
        )

    def _get_application_stylesheet(self, theme_config: ThemeConfig) -> str:
        """Get cached or generate application stylesheet"""
        if theme_config.mode in self._stylesheet_cache:
            return self._stylesheet_cache[theme_config.mode]

        stylesheet = self._generate_application_stylesheet(theme_config)
        self._stylesheet_cache[theme_config.mode] = stylesheet
        return stylesheet

    def _generate_application_stylesheet(self, theme_config: ThemeConfig) -> str:
        """Generate complete application stylesheet"""
        colors = theme_config.colors

        # Main window styling
        main_window_style = f"""
        QMainWindow {{
            background-color: {colors.background};
            color: {colors.on_background};
        }}
        """

        # Text edit (chat display) styling
        text_edit_style = f"""
        QTextEdit {{
            background-color: {theme_config.chat_background};
            color: {colors.on_surface};
            border: 1px solid {colors.outline_variant};
            border-radius: 8px;
            padding: 12px;
            /* Font will be set programmatically via setFont() to respect user preferences */
            line-height: 1.4;
            selection-background-color: {colors.primary_container};
            selection-color: {colors.on_primary_container};
        }}

        QTextEdit:focus {{
            border: 2px solid {colors.primary};
        }}
        """

        # Line edit (message input) styling
        line_edit_style = f"""
        QLineEdit {{
            background-color: {theme_config.input_background};
            color: {colors.on_surface};
            border: 1px solid {colors.outline_variant};
            border-radius: 6px;
            padding: 8px 12px;
            /* Font will be set programmatically via setFont() to respect user preferences */
            min-height: 20px;
        }}

        QLineEdit:focus {{
            border: 2px solid {colors.primary};
            background-color: {colors.surface_variant};
        }}

        QLineEdit:hover {{
            border-color: {colors.outline};
        }}
        """

        # Button styling
        button_style = f"""
        QPushButton {{
            background-color: {theme_config.button_background};
            color: {colors.on_primary};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
            min-width: 80px;
            min-height: 32px;
        }}

        QPushButton:hover {{
            background-color: {theme_config.button_hover};
        }}

        QPushButton:pressed {{
            background-color: {colors.primary_container};
        }}

        QPushButton:disabled {{
            background-color: {colors.surface_variant};
            color: {colors.on_surface_variant};
        }}
        """

        # Label styling
        label_style = f"""
        QLabel {{
            color: {colors.on_surface};
            font-size: 12px;
        }}

        QLabel[class="status-connected"] {{
            color: {theme_config.status_connected};
            font-weight: bold;
        }}

        QLabel[class="status-disconnected"] {{
            color: {theme_config.status_disconnected};
            font-weight: bold;
        }}

        QLabel[class="status-connecting"] {{
            color: {theme_config.status_connecting};
            font-weight: bold;
        }}

        QLabel[class="backend-info"] {{
            color: {colors.on_surface_variant};
            font-size: 10px;
            padding: 5px;
        }}
        """

        # Scrollbar styling
        scrollbar_style = f"""
        QScrollBar:vertical {{
            background-color: {colors.surface_variant};
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors.outline};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors.on_surface_variant};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
        }}
        """

        # Menu bar and status bar (if added later)
        menu_style = f"""
        QMenuBar {{
            background-color: {colors.surface};
            color: {colors.on_surface};
            border-bottom: 1px solid {colors.outline_variant};
        }}

        QMenuBar::item {{
            padding: 4px 8px;
            background-color: transparent;
        }}

        QMenuBar::item:selected {{
            background-color: {colors.surface_variant};
        }}

        QStatusBar {{
            background-color: {colors.surface};
            color: {colors.on_surface};
            border-top: 1px solid {colors.outline_variant};
        }}
        """

        # Combine all styles
        complete_stylesheet = f"""
        /* Material Design 3 Theme: {theme_config.name} */
        {main_window_style}
        {text_edit_style}
        {line_edit_style}
        {button_style}
        {label_style}
        {scrollbar_style}
        {menu_style}
        """

        return complete_stylesheet.strip()

    def clear_cache(self) -> None:
        """Clear stylesheet cache (useful for theme updates)"""
        self._stylesheet_cache.clear()
        self.logger.info(
            "Theme stylesheet cache cleared",
            theme_event="cache_cleared",
            module=__name__,
        )


# Export only necessary symbols per PROJECT_RULES.md
__all__ = ["ThemeApplier"]
