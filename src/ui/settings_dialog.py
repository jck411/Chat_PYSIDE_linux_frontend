"""
Refactored Settings Dialog

Following PROJECT_RULES.md:
- ≤ 150 LOC main dialog
- Composition over inheritance
- Component-based architecture
"""

from typing import Any

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
)

from .backend_settings_widget import BackendSettingsWidget
from .ui_settings_widget import UISettingsWidget


class SettingsDialog(QDialog):
    """
    Main settings dialog that orchestrates all setting widgets.

    Following PROJECT_RULES.md:
    - Composed of focused widgets
    - Signal-based updates
    - Type-safe initialization
    """    # Signals (aggregate from child components)
    backend_changed = Signal(str)  # profile_id
    theme_changed = Signal(str)  # theme name
    font_changed = Signal()  # font configuration changed

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = structlog.get_logger(__name__)

        self._setup_ui()
        self._connect_signals()

        self.logger.info(
            "Refactored settings dialog initialized",
            ui_event="settings_dialog_init",
            module=__name__,
        )

    def _setup_ui(self) -> None:
        """Setup the settings dialog UI with component widgets"""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Tab widget for different settings categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create component widgets
        self.backend_widget = BackendSettingsWidget(self)
        self.ui_widget = UISettingsWidget(self)

        # Add tabs
        self.tab_widget.addTab(self.backend_widget, "Backend")
        self.tab_widget.addTab(self.ui_widget, "UI")

        # Button box
        button_layout = QHBoxLayout()

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._ok_clicked)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect child widget signals to main dialog signals"""
        # Forward signals from child components
        self.backend_widget.backend_changed.connect(self.backend_changed.emit)
        self.ui_widget.theme_changed.connect(self.theme_changed.emit)
        self.ui_widget.font_changed.connect(self.font_changed.emit)

    def _apply_settings(self) -> None:
        """Apply settings from all component widgets"""
        try:
            # Apply settings from each component
            self.backend_widget.apply_settings()
            self.ui_widget.apply_settings()

            self.logger.info(
                "Settings applied successfully",
                ui_event="settings_applied",
                module=__name__,
            )

        except (AttributeError, TypeError) as e:
            self.logger.error(
                "Widget method call failed - invalid widget state",
                ui_event="settings_apply_widget_error",
                module=__name__,
                error=str(e),
            )
        except OSError as e:
            self.logger.error(
                "Failed to save settings to file",
                ui_event="settings_apply_io_error",
                module=__name__,
                error=str(e),
            )
        except (ValueError, KeyError) as e:
            self.logger.error(
                "Invalid settings configuration data",
                ui_event="settings_apply_data_error",
                module=__name__,
                error=str(e),
            )
        except Exception as e:
            self.logger.error(
                "Unexpected error applying settings",
                ui_event="settings_apply_unexpected_error",
                module=__name__,
                error=str(e),
                error_type=type(e).__name__,
            )

    def _ok_clicked(self) -> None:
        """Handle OK button click - apply settings and close"""
        self._apply_settings()
        self.accept()

    def cleanup(self) -> None:
        """Clean up resources when dialog is closed"""
        try:
            # Cleanup component widgets if they have cleanup methods
            for widget_name in ['backend_widget', 'ui_widget']:
                widget = getattr(self, widget_name, None)
                if widget and hasattr(widget, 'cleanup'):
                    try:
                        widget.cleanup()
                    except Exception as widget_error:
                        self.logger.warning(
                            f"Error cleaning up {widget_name}",
                            ui_event="widget_cleanup_error",
                            module=__name__,
                            widget=widget_name,
                            error=str(widget_error),
                        )

            self.logger.info(
                "Settings dialog cleanup completed",
                ui_event="settings_dialog_cleanup",
                module=__name__,
            )

        except Exception as e:
            self.logger.error(
                "Error during settings dialog cleanup",
                ui_event="settings_dialog_cleanup_error",
                module=__name__,
                error=str(e),
                error_type=type(e).__name__,
            )

    def closeEvent(self, event: Any) -> None:
        """Handle close event with proper cleanup"""
        self.cleanup()
        super().closeEvent(event)


# Export only the main dialog class per PROJECT_RULES.md
__all__ = ["SettingsDialog"]
