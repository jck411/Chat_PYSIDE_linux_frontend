"""
Backend Settings Widget

Following PROJECT_RULES.md:
- ≤ 150 LOC focused component
- Single responsibility principle
- Clean signal-based communication
"""

from typing import Any

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config import get_config_manager


class BackendSettingsWidget(QWidget):
    """Widget for managing backend connection profiles."""

    backend_changed = Signal(str)  # profile_id

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = structlog.get_logger(__name__)
        self.config_manager = get_config_manager()
        self.is_new_profile_mode = False

        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self) -> None:
        """Setup backend settings UI"""
        layout = QVBoxLayout(self)

        # Backend selection
        selection_group = QGroupBox("Backend Selection")
        selection_layout = QFormLayout(selection_group)

        self.backend_combo = QComboBox()
        self.backend_combo.currentTextChanged.connect(self._on_backend_selection_changed)
        selection_layout.addRow("Active Backend:", self.backend_combo)
        layout.addWidget(selection_group)

        # Connection details
        details_group = QGroupBox("Connection Details")
        details_layout = QFormLayout(details_group)

        self.host_edit = QLineEdit()
        self.host_edit.textChanged.connect(self._update_websocket_preview)
        details_layout.addRow("Host:", self.host_edit)

        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(8000)
        self.port_edit.valueChanged.connect(self._update_websocket_preview)
        details_layout.addRow("Port:", self.port_edit)

        self.ssl_checkbox = QCheckBox("Use SSL/TLS")
        self.ssl_checkbox.toggled.connect(self._update_websocket_preview)
        details_layout.addRow("Security:", self.ssl_checkbox)

        # WebSocket URL preview
        self.websocket_url_label = QLabel("N/A")
        self.websocket_url_label.setProperty("class", "websocket-url")
        details_layout.addRow("WebSocket URL:", self.websocket_url_label)

        layout.addWidget(details_group)

        # Profile management buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._save_current_profile)
        button_layout.addWidget(self.save_button)

        self.add_button = QPushButton("Add New")
        self.add_button.clicked.connect(self._add_new_profile)
        button_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_current_profile)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)
        self._update_ui_mode()

    def _load_current_settings(self) -> None:
        """Load current backend settings"""
        profiles = self.config_manager.list_backend_profiles()
        active_profile_id = self.config_manager.get_active_backend_id()

        self.backend_combo.clear()
        for profile_id, profile_name in profiles.items():
            self.backend_combo.addItem(profile_name, profile_id)

        if active_profile_id:
            index = self.backend_combo.findData(active_profile_id)
            if index >= 0:
                self.backend_combo.setCurrentIndex(index)

        self._update_backend_details()

    def _update_backend_details(self) -> None:
        """Update backend editing fields with selected profile"""
        profile_id = self.backend_combo.currentData()
        if profile_id:
            profile = self.config_manager.get_backend_profile(profile_id)
            if profile:
                self.host_edit.setText(profile.host)
                self.port_edit.setValue(profile.port)
                self.ssl_checkbox.setChecked(profile.use_ssl)
                self._update_websocket_preview()
            else:
                self._clear_backend_details()
        else:
            self._clear_backend_details()

    def _clear_backend_details(self) -> None:
        """Clear backend editing fields"""
        self.host_edit.clear()
        self.port_edit.setValue(8000)
        self.ssl_checkbox.setChecked(False)
        self.websocket_url_label.setText("N/A")

    def _on_backend_selection_changed(self) -> None:
        """Handle backend selection change"""
        if not self.is_new_profile_mode:
            self._update_backend_details()
        self._update_ui_mode()

    def _update_websocket_preview(self) -> None:
        """Update the WebSocket URL preview"""
        try:
            host = self.host_edit.text().strip()
            port = self.port_edit.value()
            use_ssl = self.ssl_checkbox.isChecked()

            if host:
                protocol = "wss" if use_ssl else "ws"
                url = f"{protocol}://{host}:{port}/ws/chat"
                self.websocket_url_label.setText(url)
            else:
                self.websocket_url_label.setText("Enter host to see URL preview")
        except Exception as e:
            self.logger.error("Websocket preview failed", error=str(e))

    def _save_current_profile(self) -> None:
        """Save changes to the current backend profile"""
        profile_id = self.backend_combo.currentData()
        if not profile_id:
            return

        host = self.host_edit.text().strip()
        port = self.port_edit.value()
        use_ssl = self.ssl_checkbox.isChecked()

        if not host:
            return

        current_profile = self.config_manager.get_backend_profile(profile_id)
        if current_profile:
            self.config_manager.update_backend_profile(
                profile_id,
                current_profile.name,
                host,
                port,
                use_ssl,
                current_profile.description,
            )

            if profile_id == self.config_manager.get_active_backend_id():
                self.backend_changed.emit(profile_id)

    def _add_new_profile(self) -> None:
        """Add a new backend profile (placeholder)"""
        pass

    def _delete_current_profile(self) -> None:
        """Delete the currently selected backend profile (placeholder)"""
        pass

    def _update_ui_mode(self) -> None:
        """Update UI elements based on current mode"""
        has_selection = bool(self.backend_combo.currentData())
        self.save_button.setEnabled(has_selection and not self.is_new_profile_mode)
        self.delete_button.setEnabled(has_selection and not self.is_new_profile_mode)

    def apply_settings(self) -> None:
        """Apply current backend selection"""
        selected_profile_id = self.backend_combo.currentData()
        current_active_id = self.config_manager.get_active_backend_id()

        if selected_profile_id and selected_profile_id != current_active_id:
            self.config_manager.set_active_backend(selected_profile_id)
            self.backend_changed.emit(selected_profile_id)

    def cleanup(self) -> None:
        """Clean up resources and disconnect signals"""
        try:
            # Disconnect all signals to prevent memory leaks
            try:
                self.backend_changed.disconnect()
            except (TypeError, RuntimeError):
                # Signal may already be disconnected or not connected
                pass

            self.logger.info(
                "Backend settings widget cleanup completed",
                ui_event="backend_widget_cleanup",
                module=__name__,
            )

        except Exception as e:
            self.logger.error(
                "Error during backend settings widget cleanup",
                ui_event="backend_widget_cleanup_error",
                module=__name__,
                error=str(e),
                error_type=type(e).__name__,
            )


__all__ = ["BackendSettingsWidget"]
