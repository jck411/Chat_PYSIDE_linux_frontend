"""
Backend Settings Widget

Following PROJECT_RULES.md:
- ≤ 150 LOC focused component
- Single responsibility principle
- Clean signal-based communication
"""

import uuid
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
        self.original_values = {}  # Track original values for edit detection

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

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_field_changed)
        details_layout.addRow("Profile Name:", self.name_edit)

        self.host_edit = QLineEdit()
        self.host_edit.textChanged.connect(self._on_field_changed)
        details_layout.addRow("Host:", self.host_edit)

        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(8000)
        self.port_edit.valueChanged.connect(self._on_field_changed)
        details_layout.addRow("Port:", self.port_edit)

        self.ssl_checkbox = QCheckBox("Use SSL/TLS")
        self.ssl_checkbox.toggled.connect(self._on_field_changed)
        details_layout.addRow("Security:", self.ssl_checkbox)

        # WebSocket URL preview
        self.websocket_url_label = QLabel("N/A")
        self.websocket_url_label.setProperty("class", "websocket-url")
        details_layout.addRow("WebSocket URL:", self.websocket_url_label)

        layout.addWidget(details_group)

        # Profile management buttons
        button_layout = QHBoxLayout()

        self.action_button = QPushButton("Add New")
        self.action_button.clicked.connect(self._handle_action_button)
        button_layout.addWidget(self.action_button)

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
        if profile_id and not self.is_new_profile_mode:
            profile = self.config_manager.get_backend_profile(profile_id)
            if profile:
                self.name_edit.setText(profile.name)
                self.host_edit.setText(profile.host)
                self.port_edit.setValue(profile.port)
                self.ssl_checkbox.setChecked(profile.use_ssl)
                self._store_original_values(profile)
                self._update_websocket_preview()
            else:
                self._clear_backend_details()
        elif not self.is_new_profile_mode:
            self._clear_backend_details()

    def _store_original_values(self, profile) -> None:
        """Store original values for change detection"""
        self.original_values = {
            "name": profile.name,
            "host": profile.host,
            "port": profile.port,
            "use_ssl": profile.use_ssl,
        }

    def _has_changes(self) -> bool:
        """Check if current values differ from original"""
        if self.is_new_profile_mode:
            return bool(self.name_edit.text().strip() or self.host_edit.text().strip())

        return (
            self.name_edit.text().strip() != self.original_values.get("name", "") or
            self.host_edit.text().strip() != self.original_values.get("host", "") or
            self.port_edit.value() != self.original_values.get("port", 8000) or
            self.ssl_checkbox.isChecked() != self.original_values.get("use_ssl", False)
        )

    def _clear_backend_details(self) -> None:
        """Clear backend editing fields"""
        self.name_edit.clear()
        self.host_edit.clear()
        self.port_edit.setValue(8000)
        self.ssl_checkbox.setChecked(False)
        self.websocket_url_label.setText("N/A")
        self.original_values.clear()

    def _on_backend_selection_changed(self) -> None:
        """Handle backend selection change"""
        if not self.is_new_profile_mode:
            self._update_backend_details()
        self._update_ui_mode()

    def _on_field_changed(self) -> None:
        """Handle field value changes"""
        self._update_websocket_preview()
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

    def _handle_action_button(self) -> None:
        """Handle action button click (Add New or Save)"""
        has_changes = self._has_changes()
        current_profile = self.backend_combo.currentData()

        self.logger.debug(
            "Action button clicked",
            is_new_profile_mode=self.is_new_profile_mode,
            has_changes=has_changes,
            current_profile=current_profile,
            button_text=self.action_button.text(),
        )

        if self.is_new_profile_mode:
            self._save_new_profile()
        else:
            # Check if we have changes to an existing profile
            if has_changes and current_profile:
                self._save_current_profile()
            else:
                self._start_new_profile_mode()

    def _start_new_profile_mode(self) -> None:
        """Start creating a new profile"""
        self.is_new_profile_mode = True
        self._clear_backend_details()
        self.backend_combo.setEnabled(False)
        self._update_ui_mode()

    def _save_new_profile(self) -> None:
        """Save new profile"""
        name = self.name_edit.text().strip()
        host = self.host_edit.text().strip()
        port = self.port_edit.value()
        use_ssl = self.ssl_checkbox.isChecked()

        if not name or not host:
            self.logger.warning("Profile name and host are required")
            return

        try:
            # Generate unique profile ID
            profile_id = f"profile_{uuid.uuid4().hex[:8]}"

            self.config_manager.add_backend_profile(
                profile_id, name, host, port, use_ssl, f"Custom profile: {name}"
            )            # Exit new profile mode and reload
            self.is_new_profile_mode = False
            self.backend_combo.setEnabled(True)
            self._load_current_settings()

            # Select the newly created profile
            index = self.backend_combo.findData(profile_id)
            if index >= 0:
                self.backend_combo.setCurrentIndex(index)

            self.logger.info(
                "New backend profile created",
                profile_id=profile_id,
                name=name,
                host=host,
            )

        except Exception as e:
            self.logger.error("Failed to create new profile", error=str(e))

    def _save_current_profile(self) -> None:
        """Save changes to the current backend profile"""
        profile_id = self.backend_combo.currentData()
        if not profile_id:
            return

        name = self.name_edit.text().strip()
        host = self.host_edit.text().strip()
        port = self.port_edit.value()
        use_ssl = self.ssl_checkbox.isChecked()

        if not name or not host:
            self.logger.warning("Profile name and host are required")
            return

        try:
            current_profile = self.config_manager.get_backend_profile(profile_id)
            if current_profile:
                self.config_manager.update_backend_profile(
                    profile_id, name, host, port, use_ssl, current_profile.description
                )

                # Update stored values
                self.original_values = {
                    "name": name,
                    "host": host,
                    "port": port,
                    "use_ssl": use_ssl,
                }

                # Reload the combo box to reflect any name changes
                current_selection = profile_id
                self._load_current_settings()

                # Restore selection
                index = self.backend_combo.findData(current_selection)
                if index >= 0:
                    self.backend_combo.setCurrentIndex(index)

                if profile_id == self.config_manager.get_active_backend_id():
                    self.backend_changed.emit(profile_id)

                self._update_ui_mode()
                self.logger.info("Backend profile updated", profile_id=profile_id)

        except Exception as e:
            self.logger.error("Failed to update profile", error=str(e))

    def _delete_current_profile(self) -> None:
        """Delete the currently selected backend profile"""
        profile_id = self.backend_combo.currentData()
        if not profile_id:
            return

        try:
            self.config_manager.remove_backend_profile(profile_id)
            self._load_current_settings()
            self.logger.info("Backend profile deleted", profile_id=profile_id)
        except Exception as e:
            self.logger.error("Failed to delete profile", error=str(e))

    def _update_ui_mode(self) -> None:
        """Update UI elements based on current mode"""
        has_selection = bool(self.backend_combo.currentData())
        has_changes = self._has_changes()

        self.logger.debug(
            "Updating UI mode",
            is_new_profile_mode=self.is_new_profile_mode,
            has_selection=has_selection,
            has_changes=has_changes,
            current_profile_id=self.backend_combo.currentData(),
        )

        if self.is_new_profile_mode:
            self.action_button.setText("Save New")
            self.action_button.setEnabled(has_changes)
            self.delete_button.setEnabled(False)
        else:
            if has_changes and has_selection:
                self.action_button.setText("Save Changes")
            else:
                self.action_button.setText("Add New")

            self.action_button.setEnabled(True)
            self.delete_button.setEnabled(has_selection and not self.is_new_profile_mode)

    def apply_settings(self) -> None:
        """Apply current backend selection"""
        # If in new profile mode, save the profile first
        if self.is_new_profile_mode and self._has_changes():
            self._save_new_profile()

        # If there are unsaved changes to existing profile, save them
        if not self.is_new_profile_mode and self._has_changes():
            self._save_current_profile()

        # Apply backend selection
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
