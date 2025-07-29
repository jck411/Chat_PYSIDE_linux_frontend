"""
Settings Dialog for Chat Frontend

Following PROJECT_RULES.md:
- ≤ 150 LOC with ≤ 2 public symbols per UI controller
- Keep UI thread under 10ms per frame
- Structured logging integration
"""

from typing import Any

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import ThemePreference, get_config_manager
from ..themes import ThemeMode, get_theme_manager


class SettingsDialog(QDialog):
    """
    Settings dialog for managing application configuration.

    Provides UI for:
    - Backend profile management
    - Theme preferences
    - Other application settings
    """

    # Signals
    backend_changed = Signal(str)  # profile_id
    theme_changed = Signal(str)  # theme name
    font_changed = Signal()  # font configuration changed

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.logger = structlog.get_logger(__name__)
        self.config_manager = get_config_manager()

        self._setup_ui()
        self._load_current_settings()

        self.logger.info(
            "Settings dialog initialized",
            ui_event="settings_dialog_init",
            module=__name__,
        )

    def _setup_ui(self) -> None:
        """Setup the settings dialog UI"""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Tab widget for different settings categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Backend settings tab
        self._setup_backend_tab()

        # UI settings tab
        self._setup_ui_tab()

        # Font settings tab
        self._setup_font_tab()

        # Button box
        button_layout = QHBoxLayout()

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)
        self.apply_button.setStyleSheet(
            """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
            }
        """
        )

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._ok_clicked)
        self.ok_button.setStyleSheet(
            """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
            }
        """
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
            }
        """
        )

        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _setup_backend_tab(self) -> None:
        """Setup backend configuration tab"""
        backend_widget = QWidget()
        layout = QVBoxLayout(backend_widget)

        # Backend selection with mode controls
        selection_group = QGroupBox("Backend Profiles")
        selection_layout = QVBoxLayout(selection_group)

        # Profile selection row
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Active Profile:"))

        self.backend_combo = QComboBox()
        self.backend_combo.currentTextChanged.connect(
            self._on_backend_selection_changed
        )
        profile_row.addWidget(self.backend_combo)

        # Mode control buttons
        self.new_profile_button = QPushButton("New")
        self.new_profile_button.clicked.connect(self._enter_new_profile_mode)
        self.new_profile_button.setStyleSheet(
            """
            QPushButton {
                background-color: #38a169;
                color: white;
                border: 1px solid #2f855a;
                padding: 2px 6px;
                border-radius: 2px;
                font-size: 12px;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: #2f855a;
            }
            QPushButton:pressed {
                background-color: #276749;
            }
        """
        )

        self.delete_profile_button = QPushButton("Delete")
        self.delete_profile_button.clicked.connect(self._delete_current_profile)
        self.delete_profile_button.setStyleSheet(
            """
            QPushButton {
                background-color: #e53e3e;
                color: white;
                border: 1px solid #c53030;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 35px;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
            QPushButton:pressed {
                background-color: #9c2626;
            }
        """
        )

        profile_row.addWidget(self.new_profile_button)
        profile_row.addWidget(self.delete_profile_button)
        profile_row.addStretch()

        selection_layout.addLayout(profile_row)
        layout.addWidget(selection_group)

        # Dynamic profile editing section
        self.profile_edit_group = QGroupBox()
        edit_layout = QFormLayout(self.profile_edit_group)

        # Profile name (only shown in new mode)
        self.profile_name_edit = QLineEdit()
        self.profile_name_edit.setPlaceholderText("Enter profile name...")
        self.profile_name_label = QLabel("Profile Name:")
        edit_layout.addRow(self.profile_name_label, self.profile_name_edit)

        # Connection details
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("e.g., 192.168.1.223")

        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(8000)

        self.ssl_checkbox = QCheckBox("Use SSL/TLS")

        self.websocket_url_label = QLabel()
        self.websocket_url_label.setStyleSheet(
            "color: gray; font-style: italic; font-size: 11px;"
        )

        edit_layout.addRow("Host:", self.host_edit)
        edit_layout.addRow("Port:", self.port_edit)
        edit_layout.addRow("", self.ssl_checkbox)
        edit_layout.addRow("WebSocket URL:", self.websocket_url_label)

        # Connect signals to update URL preview and button state
        self.host_edit.textChanged.connect(self._update_websocket_preview)
        self.host_edit.textChanged.connect(self._update_action_button_state)
        self.port_edit.valueChanged.connect(self._update_websocket_preview)
        self.ssl_checkbox.toggled.connect(self._update_websocket_preview)
        self.profile_name_edit.textChanged.connect(self._update_action_button_state)

        layout.addWidget(self.profile_edit_group)

        # Dynamic action button
        action_layout = QHBoxLayout()

        self.action_button = QPushButton()
        self.action_button.clicked.connect(self._handle_action_button)
        self.action_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: 1px solid #2d3748;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
            QPushButton:pressed {
                background-color: #1a202c;
            }
            QPushButton:disabled {
                background-color: #a0aec0;
                border-color: #718096;
                color: #4a5568;
            }
        """
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel_new_profile_mode)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #4a5568;
                border: 1px solid #cbd5e0;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f7fafc;
                border-color: #a0aec0;
            }
        """
        )

        action_layout.addStretch()
        action_layout.addWidget(self.cancel_button)
        action_layout.addWidget(self.action_button)

        layout.addLayout(action_layout)
        layout.addStretch()

        # Initialize mode
        self.is_new_profile_mode = False
        self._update_ui_mode()

        self.tab_widget.addTab(backend_widget, "Backend")

    def _setup_ui_tab(self) -> None:
        """Setup UI preferences tab"""
        ui_widget = QWidget()
        layout = QVBoxLayout(ui_widget)

        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", ThemePreference.LIGHT.value)
        self.theme_combo.addItem("Dark", ThemePreference.DARK.value)
        self.theme_combo.addItem("System", ThemePreference.SYSTEM.value)

        theme_layout.addRow("Theme:", self.theme_combo)
        layout.addWidget(theme_group)

        # Window settings
        window_group = QGroupBox("Window")
        window_layout = QFormLayout(window_group)

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(400, 2000)
        self.width_spinbox.setSuffix(" px")

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(300, 1500)
        self.height_spinbox.setSuffix(" px")

        window_layout.addRow("Default Width:", self.width_spinbox)
        window_layout.addRow("Default Height:", self.height_spinbox)

        layout.addWidget(window_group)

        layout.addStretch()
        self.tab_widget.addTab(ui_widget, "UI")

    def _setup_font_tab(self) -> None:
        """Setup font preferences tab"""
        font_widget = QWidget()
        layout = QVBoxLayout(font_widget)

        # Chat font settings
        chat_font_group = QGroupBox("Chat Font")
        chat_font_layout = QFormLayout(chat_font_group)

        self.chat_font_combo = QFontComboBox()
        self.chat_font_combo.setCurrentFont("monospace")

        self.chat_font_size_spinbox = QSpinBox()
        self.chat_font_size_spinbox.setRange(8, 24)
        self.chat_font_size_spinbox.setValue(10)
        self.chat_font_size_spinbox.setSuffix(" pt")

        chat_font_layout.addRow("Font Family:", self.chat_font_combo)
        chat_font_layout.addRow("Font Size:", self.chat_font_size_spinbox)
        layout.addWidget(chat_font_group)

        # UI font settings
        ui_font_group = QGroupBox("Interface Font")
        ui_font_layout = QFormLayout(ui_font_group)

        self.ui_font_combo = QFontComboBox()
        self.ui_font_combo.setCurrentFont("sans-serif")

        self.ui_font_size_spinbox = QSpinBox()
        self.ui_font_size_spinbox.setRange(8, 16)
        self.ui_font_size_spinbox.setValue(9)
        self.ui_font_size_spinbox.setSuffix(" pt")

        ui_font_layout.addRow("Font Family:", self.ui_font_combo)
        ui_font_layout.addRow("Font Size:", self.ui_font_size_spinbox)
        layout.addWidget(ui_font_group)

        layout.addStretch()
        self.tab_widget.addTab(font_widget, "Fonts")

    def _load_current_settings(self) -> None:
        """Load current settings into the dialog"""
        # Load backend profiles
        profiles = self.config_manager.list_backend_profiles()
        active_profile_id = self.config_manager.get_active_backend_id()

        self.backend_combo.clear()
        for profile_id, profile_name in profiles.items():
            self.backend_combo.addItem(profile_name, profile_id)

        # Set active backend
        if active_profile_id:
            index = self.backend_combo.findData(active_profile_id)
            if index >= 0:
                self.backend_combo.setCurrentIndex(index)

        # Update backend details
        self._update_backend_details()

        # Load theme preference - check both config manager and theme manager
        current_theme = self.config_manager.get_theme_preference()
        theme_manager = get_theme_manager()
        current_theme_mode = theme_manager.current_mode

        self.logger.info(
            "Loading current theme settings",
            ui_event="loading_theme_settings",
            module=__name__,
            config_theme=current_theme.value,
            theme_manager_mode=current_theme_mode.value,
        )

        # Use theme manager's current mode as the source of truth
        theme_index = self.theme_combo.findData(current_theme_mode.value)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        else:
            # Fallback to config manager
            theme_index = self.theme_combo.findData(current_theme.value)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)

        # Load window geometry
        geometry = self.config_manager.get_window_geometry()
        self.width_spinbox.setValue(geometry["width"])
        self.height_spinbox.setValue(geometry["height"])

        # Load font configuration
        font_config = self.config_manager.get_font_config()
        self.chat_font_combo.setCurrentFont(font_config["chat_font_family"])
        self.chat_font_size_spinbox.setValue(font_config["chat_font_size"])
        self.ui_font_combo.setCurrentFont(font_config["ui_font_family"])
        self.ui_font_size_spinbox.setValue(font_config["ui_font_size"])

    def _update_backend_details(self) -> None:
        """Update backend editing fields with selected profile"""
        profile_id = self.backend_combo.currentData()
        if profile_id:
            profile = self.config_manager.get_backend_profile(profile_id)
            if profile:
                # Update editing fields
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
            self.logger.error(
                "Failed to update websocket preview",
                ui_event="websocket_preview_failed",
                module=__name__,
                error=str(e),
            )

    def _save_current_profile(self) -> None:
        """Save changes to the current backend profile"""
        try:
            profile_id = self.backend_combo.currentData()
            if not profile_id:
                return

            host = self.host_edit.text().strip()
            port = self.port_edit.value()
            use_ssl = self.ssl_checkbox.isChecked()

            if not host:
                return

            # Get current profile to preserve name and description
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

                self.logger.info(
                    "Backend profile updated",
                    ui_event="profile_updated",
                    module=__name__,
                    profile_id=profile_id,
                    host=host,
                    port=port,
                    ssl=use_ssl,
                )

                # If this is the active profile, emit backend changed signal
                if profile_id == self.config_manager.get_active_backend_id():
                    self.backend_changed.emit(profile_id)

        except Exception as e:
            self.logger.error(
                "Failed to save backend profile",
                ui_event="profile_save_failed",
                module=__name__,
                error=str(e),
            )

    def _add_new_profile(self) -> None:
        """Add a new backend profile"""
        try:
            host = self.host_edit.text().strip()
            port = self.port_edit.value()
            use_ssl = self.ssl_checkbox.isChecked()
            profile_name = self.profile_name_edit.text().strip()

            if not host or not profile_name:
                return

            # Generate a unique profile ID
            profiles = self.config_manager.list_backend_profiles()
            profile_count = len(profiles) + 1
            profile_id = f"custom_{profile_count}"

            # Ensure unique ID
            while profile_id in profiles:
                profile_count += 1
                profile_id = f"custom_{profile_count}"

            self.config_manager.add_backend_profile(
                profile_id,
                profile_name,
                host,
                port,
                use_ssl,
                "User-created backend profile",
            )

            # Add to combo box and select it
            self.backend_combo.addItem(profile_name, profile_id)
            index = self.backend_combo.findData(profile_id)
            if index >= 0:
                self.backend_combo.setCurrentIndex(index)

            # Clear the profile name field for next use
            self.profile_name_edit.clear()

            self.logger.info(
                "New backend profile added",
                ui_event="profile_added",
                module=__name__,
                profile_id=profile_id,
                profile_name=profile_name,
                host=host,
                port=port,
                ssl=use_ssl,
            )

        except Exception as e:
            self.logger.error(
                "Failed to add backend profile",
                ui_event="profile_add_failed",
                module=__name__,
                error=str(e),
            )

    def _delete_current_profile(self) -> None:
        """Delete the currently selected backend profile"""
        try:
            profile_id = self.backend_combo.currentData()
            if not profile_id:
                self.logger.warning(
                    "No profile selected for deletion",
                    ui_event="delete_no_profile",
                    module=__name__,
                )
                return

            # Check if this is the default profile
            if profile_id == "default":
                self.logger.warning(
                    "Cannot delete default profile",
                    ui_event="delete_default_blocked",
                    module=__name__,
                    profile_id=profile_id,
                )
                return

            # Check if this is the active profile
            active_profile_id = self.config_manager.get_active_backend_id()
            if profile_id == active_profile_id:
                self.logger.warning(
                    "Cannot delete active profile",
                    ui_event="delete_active_blocked",
                    module=__name__,
                    profile_id=profile_id,
                    active_profile_id=active_profile_id,
                )
                return

            # Get profile name for logging
            profile = self.config_manager.get_backend_profile(profile_id)
            profile_name = profile.name if profile else "Unknown"

            self.logger.info(
                "Attempting to delete profile",
                ui_event="delete_attempt",
                module=__name__,
                profile_id=profile_id,
                profile_name=profile_name,
                active_profile_id=active_profile_id,
            )

            # Remove from config manager
            self.config_manager.remove_backend_profile(profile_id)

            # Remove from combo box
            index = self.backend_combo.findData(profile_id)
            if index >= 0:
                self.backend_combo.removeItem(index)

            # Clear fields if this was the selected profile
            self._clear_backend_details()

            self.logger.info(
                "Backend profile deleted successfully",
                ui_event="profile_deleted",
                module=__name__,
                profile_id=profile_id,
                profile_name=profile_name,
            )

        except Exception as e:
            self.logger.error(
                "Failed to delete backend profile",
                ui_event="profile_delete_failed",
                module=__name__,
                error=str(e),
                profile_id=profile_id if "profile_id" in locals() else "unknown",
            )

    def _apply_settings(self) -> None:
        """Apply current settings"""
        try:
            # Apply backend selection
            selected_profile_id = self.backend_combo.currentData()
            current_active_id = self.config_manager.get_active_backend_id()

            if selected_profile_id and selected_profile_id != current_active_id:
                self.config_manager.set_active_backend(selected_profile_id)
                self.backend_changed.emit(selected_profile_id)
                self.logger.info(
                    "Backend profile changed",
                    ui_event="backend_changed",
                    module=__name__,
                    new_profile=selected_profile_id,
                )

            # Apply theme preference
            selected_theme_value = self.theme_combo.currentData()
            current_theme = self.config_manager.get_theme_preference()

            self.logger.info(
                "Theme change attempt",
                ui_event="theme_change_attempt",
                module=__name__,
                selected_theme=selected_theme_value,
                current_theme=current_theme.value,
            )

            if selected_theme_value != current_theme.value:
                # Update both the config manager and theme manager
                new_theme = ThemePreference(selected_theme_value)
                self.config_manager.set_theme_preference(new_theme)

                # Apply theme immediately via theme manager
                theme_manager = get_theme_manager()
                self.logger.info(
                    "Applying theme via theme manager",
                    ui_event="applying_theme",
                    module=__name__,
                    theme=selected_theme_value,
                )

                if selected_theme_value == "light":
                    theme_manager.set_theme_mode(ThemeMode.LIGHT)
                elif selected_theme_value == "dark":
                    theme_manager.set_theme_mode(ThemeMode.DARK)

                self.theme_changed.emit(selected_theme_value)

                self.logger.info(
                    "Theme applied successfully",
                    ui_event="theme_applied",
                    module=__name__,
                    theme=selected_theme_value,
                )
            else:
                self.logger.info(
                    "No theme change needed",
                    ui_event="no_theme_change",
                    module=__name__,
                )

            # Apply window geometry to current window and save as default
            current_geometry = self.config_manager.get_window_geometry()
            new_width = self.width_spinbox.value()
            new_height = self.height_spinbox.value()

            self.logger.info(
                "Window geometry change attempt",
                ui_event="geometry_change_attempt",
                module=__name__,
                current_size=f"{current_geometry['width']}x{current_geometry['height']}",
                new_size=f"{new_width}x{new_height}",
            )

            if (
                new_width != current_geometry["width"]
                or new_height != current_geometry["height"]
            ):
                # Apply to current main window immediately
                main_window = self.parent()
                if main_window and hasattr(main_window, "resize"):
                    try:
                        # Use getattr to safely call resize method
                        resize_method = getattr(main_window, "resize", None)
                        if resize_method:
                            resize_method(new_width, new_height)
                    except (AttributeError, TypeError):
                        # Ignore if resize method doesn't exist or fails
                        pass

                # Save as default for future windows
                self.config_manager.set_window_geometry(
                    new_width, new_height, current_geometry["x"], current_geometry["y"]
                )
                self.logger.info(
                    "Window geometry updated and applied",
                    ui_event="geometry_updated",
                    module=__name__,
                    new_size=f"{new_width}x{new_height}",
                )
            else:
                self.logger.info(
                    "No geometry change needed",
                    ui_event="no_geometry_change",
                    module=__name__,
                )

            # Apply font configuration
            current_font_config = self.config_manager.get_font_config()
            new_chat_font_family = self.chat_font_combo.currentFont().family()
            new_chat_font_size = self.chat_font_size_spinbox.value()
            new_ui_font_family = self.ui_font_combo.currentFont().family()
            new_ui_font_size = self.ui_font_size_spinbox.value()

            font_changed = (
                new_chat_font_family != current_font_config["chat_font_family"] or
                new_chat_font_size != current_font_config["chat_font_size"] or
                new_ui_font_family != current_font_config["ui_font_family"] or
                new_ui_font_size != current_font_config["ui_font_size"]
            )

            if font_changed:
                self.config_manager.set_font_config(
                    new_chat_font_family,
                    new_chat_font_size,
                    new_ui_font_family,
                    new_ui_font_size
                )

                # Apply font changes to current window immediately if possible
                main_window = self.parent()
                if main_window and hasattr(main_window, "apply_font_config"):
                    try:
                        # Use getattr to safely call apply_font_config method
                        apply_font_method = getattr(main_window, "apply_font_config", None)
                        if apply_font_method:
                            apply_font_method()
                    except (AttributeError, TypeError):
                        # Ignore if method doesn't exist or fails
                        pass

                # Emit font changed signal
                self.font_changed.emit()

                self.logger.info(
                    "Font configuration updated and applied",
                    ui_event="font_updated",
                    module=__name__,
                    chat_font=f"{new_chat_font_family} {new_chat_font_size}pt",
                    ui_font=f"{new_ui_font_family} {new_ui_font_size}pt",
                )
            else:
                self.logger.info(
                    "No font change needed",
                    ui_event="no_font_change",
                    module=__name__,
                )

            # No popup - just apply silently

            self.logger.info(
                "Settings applied successfully",
                ui_event="settings_applied",
                module=__name__,
            )

        except Exception as e:
            self.logger.error(
                "Failed to apply settings",
                ui_event="settings_apply_failed",
                module=__name__,
                error=str(e),
            )

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Settings Error")
            msg_box.setText(f"Failed to apply settings: {e!s}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

    def _enter_new_profile_mode(self) -> None:
        """Enter new profile creation mode"""
        self.is_new_profile_mode = True
        self._clear_backend_details()
        self.profile_name_edit.clear()
        self._update_ui_mode()
        self.profile_name_edit.setFocus()

        self.logger.info(
            "Entered new profile mode",
            ui_event="new_profile_mode_entered",
            module=__name__,
        )

    def _cancel_new_profile_mode(self) -> None:
        """Cancel new profile creation and return to edit mode"""
        self.is_new_profile_mode = False
        self._update_backend_details()  # Reload current profile data
        self._update_ui_mode()

        self.logger.info(
            "Cancelled new profile mode",
            ui_event="new_profile_mode_cancelled",
            module=__name__,
        )

    def _update_ui_mode(self) -> None:
        """Update UI elements based on current mode"""
        try:
            profile_id = self.backend_combo.currentData()

            if self.is_new_profile_mode:
                # New profile mode
                self.profile_edit_group.setTitle("Create New Profile")
                self.profile_name_label.setVisible(True)
                self.profile_name_edit.setVisible(True)
                self.action_button.setText("Create Profile")
                self.cancel_button.setVisible(True)
                self.new_profile_button.setEnabled(False)
                self.delete_profile_button.setEnabled(False)
                self.backend_combo.setEnabled(False)
                self._update_action_button_state()
            else:
                # Edit existing profile mode
                if profile_id:
                    profile = self.config_manager.get_backend_profile(profile_id)
                    profile_name = profile.name if profile else "Unknown"
                    self.profile_edit_group.setTitle(f"Edit Profile: {profile_name}")
                    self.action_button.setText(f"Update {profile_name}")
                else:
                    self.profile_edit_group.setTitle("No Profile Selected")
                    self.action_button.setText("Update Profile")

                self.profile_name_label.setVisible(False)
                self.profile_name_edit.setVisible(False)
                self.cancel_button.setVisible(False)
                self.new_profile_button.setEnabled(True)
                self.backend_combo.setEnabled(True)

                # Enable/disable delete button based on profile
                active_profile_id = self.config_manager.get_active_backend_id()
                can_delete = bool(
                    profile_id
                    and profile_id != "default"
                    and profile_id != active_profile_id
                )

                self.logger.debug(
                    "Delete button state update",
                    ui_event="delete_button_state",
                    module=__name__,
                    profile_id=profile_id,
                    active_profile_id=active_profile_id,
                    can_delete=can_delete,
                )

                self.delete_profile_button.setEnabled(can_delete)

                # Enable/disable action button based on host
                host = self.host_edit.text().strip()
                self.action_button.setEnabled(bool(host and profile_id))
        except Exception as e:
            self.logger.error(
                "Failed to update UI mode",
                ui_event="ui_mode_update_failed",
                module=__name__,
                error=str(e),
            )

    def _update_action_button_state(self) -> None:
        """Update action button enabled state based on form validity"""
        try:
            if self.is_new_profile_mode:
                host = self.host_edit.text().strip()
                profile_name = self.profile_name_edit.text().strip()
                self.action_button.setEnabled(bool(host and profile_name))
            else:
                host = self.host_edit.text().strip()
                profile_id = self.backend_combo.currentData()
                self.action_button.setEnabled(bool(host and profile_id))
        except Exception as e:
            self.logger.error(
                "Failed to update action button state",
                ui_event="action_button_update_failed",
                module=__name__,
                error=str(e),
            )

    def _handle_action_button(self) -> None:
        """Handle the dynamic action button click"""
        if self.is_new_profile_mode:
            self._create_new_profile()
        else:
            self._update_current_profile()

    def _create_new_profile(self) -> None:
        """Create a new profile and exit new profile mode"""
        try:
            host = self.host_edit.text().strip()
            port = self.port_edit.value()
            use_ssl = self.ssl_checkbox.isChecked()
            profile_name = self.profile_name_edit.text().strip()

            if not host or not profile_name:
                return

            # Generate a unique profile ID
            profiles = self.config_manager.list_backend_profiles()
            profile_count = len(profiles) + 1
            profile_id = f"custom_{profile_count}"

            # Ensure unique ID
            while profile_id in profiles:
                profile_count += 1
                profile_id = f"custom_{profile_count}"

            self.config_manager.add_backend_profile(
                profile_id,
                profile_name,
                host,
                port,
                use_ssl,
                "User-created backend profile",
            )

            # Add to combo box and select it
            self.backend_combo.addItem(profile_name, profile_id)
            index = self.backend_combo.findData(profile_id)
            if index >= 0:
                self.backend_combo.setCurrentIndex(index)

            # Exit new profile mode
            self.is_new_profile_mode = False
            self.profile_name_edit.clear()
            self._update_ui_mode()

            self.logger.info(
                "New backend profile created",
                ui_event="profile_created",
                module=__name__,
                profile_id=profile_id,
                profile_name=profile_name,
                host=host,
                port=port,
                ssl=use_ssl,
            )

        except Exception as e:
            self.logger.error(
                "Failed to create backend profile",
                ui_event="profile_create_failed",
                module=__name__,
                error=str(e),
            )

    def _update_current_profile(self) -> None:
        """Update the currently selected profile"""
        try:
            profile_id = self.backend_combo.currentData()
            if not profile_id:
                return

            host = self.host_edit.text().strip()
            port = self.port_edit.value()
            use_ssl = self.ssl_checkbox.isChecked()

            if not host:
                return

            # Get current profile to preserve name and description
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

                self.logger.info(
                    "Backend profile updated",
                    ui_event="profile_updated",
                    module=__name__,
                    profile_id=profile_id,
                    host=host,
                    port=port,
                    ssl=use_ssl,
                )

                # If this is the active profile, emit backend changed signal
                if profile_id == self.config_manager.get_active_backend_id():
                    self.backend_changed.emit(profile_id)

        except Exception as e:
            self.logger.error(
                "Failed to update backend profile",
                ui_event="profile_update_failed",
                module=__name__,
                error=str(e),
            )

    def _ok_clicked(self) -> None:
        """Handle OK button click"""
        self._apply_settings()
        self.accept()


# Export only the dialog class per PROJECT_RULES.md
__all__ = ["SettingsDialog"]
