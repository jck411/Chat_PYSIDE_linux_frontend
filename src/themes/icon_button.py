"""
Material Design Icon Button with Theme Support

Following PROJECT_RULES.md:
- Dynamic SVG color application
- Theme-aware styling
- Performance optimized
- Signal-based updates
"""

from typing import Any

import structlog
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QPushButton

from .theme_config import ThemeConfig, ThemeMode


class MaterialIconButton(QPushButton):
    """
    Material Design icon button with dynamic color theming.

    Features:
    - SVG icon loading from resources
    - Dynamic color application based on theme
    - Proper sizing and styling
    - Theme change responsiveness
    """

    def __init__(
        self,
        icon_resource_path: str,
        size: int = 24,
        tooltip: str | None = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.logger = structlog.get_logger(__name__)

        # Icon configuration
        self._icon_resource_path = icon_resource_path
        self._icon_size = size
        self._current_theme_mode: ThemeMode | None = None

        # Setup button - make it align better with input fields
        self.setFixedSize(size + 12, size + 12)  # More padding for better alignment
        self.setIconSize(QSize(size, size))

        if tooltip:
            self.setToolTip(tooltip)

        # Apply initial styling
        self._apply_button_styling()

        # Load initial icon with default color
        self._load_initial_icon()

        self.logger.debug(
            "Material icon button created",
            icon_event="icon_button_created",
            module=__name__,
            resource_path=icon_resource_path,
            size=size,
        )

    def _load_initial_icon(self) -> None:
        """Load initial icon with default color"""
        # Use a default color that works on both themes
        default_color = "#1976D2"  # Material Blue
        icon = self._create_colored_icon(default_color)
        if icon:
            self.setIcon(icon)
            self.logger.info(
                "Initial icon loaded",
                icon_event="initial_icon_loaded",
                module=__name__,
                resource_path=self._icon_resource_path,
                color=default_color,
            )
        else:
            self.logger.error(
                "Failed to load initial icon",
                icon_event="initial_icon_failed",
                module=__name__,
                resource_path=self._icon_resource_path,
            )

    def update_theme(self, theme_config: ThemeConfig) -> None:
        """Update icon colors based on theme configuration"""
        if theme_config.mode == self._current_theme_mode:
            return  # No change needed

        self._current_theme_mode = theme_config.mode

        # Determine icon color based on theme - make it more visible
        if theme_config.mode == ThemeMode.LIGHT:
            icon_color = theme_config.colors.primary  # Dark color for light theme
        else:
            icon_color = theme_config.colors.primary  # Light color for dark theme

        # Load and color the icon
        icon = self._create_colored_icon(icon_color)
        if icon:
            self.setIcon(icon)
            self.logger.info(
                "Icon successfully loaded and applied",
                icon_event="icon_loaded",
                module=__name__,
                resource_path=self._icon_resource_path,
                icon_color=icon_color,
            )
        else:
            self.logger.error(
                "Failed to load icon",
                icon_event="icon_load_failed",
                module=__name__,
                resource_path=self._icon_resource_path,
            )

        # Update button styling
        self._apply_button_styling()

        self.logger.debug(
            "Icon theme updated",
            icon_event="icon_theme_updated",
            module=__name__,
            theme_mode=theme_config.mode.value,
            icon_color=icon_color,
        )

    def _create_colored_icon(self, color: str) -> QIcon | None:
        """Create a colored version of the SVG icon"""
        try:
            # Load SVG content from resources
            svg_renderer = QSvgRenderer(self._icon_resource_path)
            if not svg_renderer.isValid():
                self.logger.warning(
                    "Invalid SVG resource",
                    icon_event="invalid_svg",
                    module=__name__,
                    resource_path=self._icon_resource_path,
                )
                return None

            # Create pixmap with the desired size
            pixmap = QPixmap(self._icon_size, self._icon_size)
            pixmap.fill(Qt.GlobalColor.transparent)

            # Render SVG to pixmap
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            svg_renderer.render(painter)
            painter.end()

            # Apply color overlay
            colored_pixmap = QPixmap(pixmap.size())
            colored_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(colored_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceIn
            )
            painter.fillRect(colored_pixmap.rect(), color)
            painter.end()

            return QIcon(colored_pixmap)

        except Exception as e:
            self.logger.error(
                "Failed to create colored icon",
                icon_event="icon_creation_failed",
                module=__name__,
                error=str(e),
                resource_path=self._icon_resource_path,
            )
            return None

    def _apply_button_styling(self) -> None:
        """Apply Material Design button styling"""
        # Get current theme colors (will be overridden by global theme)
        if self._current_theme_mode == ThemeMode.LIGHT:
            hover_color = "rgba(25, 118, 210, 0.1)"  # Light blue with transparency
            pressed_color = "rgba(25, 118, 210, 0.2)"
        else:
            hover_color = "rgba(144, 202, 249, 0.1)"  # Light blue with transparency
            pressed_color = "rgba(144, 202, 249, 0.2)"

        # Apply minimal styling - more like a clickable icon than a button
        self.setStyleSheet(
            f"""
            QPushButton {{
                border: none;
                border-radius: 12px;
                background-color: transparent;
                padding: 4px;
            }}

            QPushButton:hover {{
                background-color: {hover_color};
            }}

            QPushButton:pressed {{
                background-color: {pressed_color};
            }}

            QPushButton:disabled {{
                opacity: 0.3;
            }}
        """
        )


# Export only necessary symbols per PROJECT_RULES.md
__all__ = ["MaterialIconButton"]
