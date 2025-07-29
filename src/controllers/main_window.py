"""
Main Window Controller for Chat Frontend

Following PROJECT_RULES.md:
- ≤ 150 LOC with ≤ 2 public symbols per UI controller
- Keep UI thread under 10ms per frame
- Immediate chunk processing without batching delays
- Structured logging with performance tracking
"""

from typing import Any

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config import get_config_manager
from ..themes import MaterialIconButton, ThemeMode, get_theme_manager
from ..ui import SettingsDialog, get_markdown_formatter
from .websocket_client import OptimizedWebSocketClient

# Import compiled resources
try:
    from .. import resources_rc
except ImportError:
    # Resources not compiled yet, will use fallback
    resources_rc = None  # type: ignore


class MainWindowController(QMainWindow):
    """
    Main chat window with optimized real-time text streaming.

    Key optimizations:
    - Direct UI updates on chunk reception (no batching)
    - Auto-scroll with smooth performance
    - Connection status monitoring
    - Minimal UI overhead for maximum speed
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = structlog.get_logger(__name__)

        # Get configuration manager
        self.config_manager = get_config_manager()

        # Initialize theme manager
        self.theme_manager = get_theme_manager()
        self._setup_theme_signals()

        # Initialize markdown formatter
        self.markdown_formatter = get_markdown_formatter()

        # Initialize WebSocket client
        self.websocket_client = OptimizedWebSocketClient()
        self._setup_websocket_signals()

        # UI state for streaming
        self._current_message_start = 0
        self._is_streaming = False
        self._current_message_id: str | None = None
        self._streaming_content = ""  # Buffer for markdown processing

        # Setup UI
        self._setup_ui()

        # Apply initial theme
        self.theme_manager.apply_current_theme()

        # Auto-connect on startup
        self.websocket_client.connect_to_backend()

        self.logger.info(
            "Main window initialized",
            window_event="main_window_init",
            module=__name__,
            backend_url=self.config_manager.get_websocket_url(),
            theme_info=self.theme_manager.get_theme_info(),
        )

    def _setup_ui(self) -> None:
        """Setup minimal, fast UI for chat streaming"""
        self.setWindowTitle("Chat PySide Frontend")

        # Load saved window geometry from configuration
        geometry = self.config_manager.get_window_geometry()
        self.setGeometry(
            geometry["x"], geometry["y"], geometry["width"], geometry["height"]
        )

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header area with connection status and icons
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)  # Improved spacing between elements

        # Left side: Connection status (clickable when disconnected)
        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet(
            "color: orange; font-weight: bold; font-size: 11px; padding: 5px;"
        )
        self.status_label.mousePressEvent = self._on_status_label_clicked
        header_layout.addWidget(self.status_label)

        # Spacer to push icons to the right
        header_layout.addStretch()

        # Right side: Material Design icons
        self._setup_header_icons(header_layout)

        layout.addLayout(header_layout)

        # Chat display - optimized for streaming with markdown support
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        # Enable HTML/rich text for markdown rendering
        self.chat_display.setAcceptRichText(True)
        layout.addWidget(self.chat_display)

        # Input area with proper alignment
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)  # Add spacing between input and button

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)

        # Material Design send icon button
        self.send_icon_button = MaterialIconButton(
            icon_resource_path=":/icons/send.svg", size=24, tooltip="Send Message"
        )
        self.send_icon_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_icon_button)
        input_layout.setAlignment(self.send_icon_button, Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(input_layout)

        # Update icon themes
        self._update_icon_themes()

    def _setup_websocket_signals(self) -> None:
        """Connect WebSocket signals for immediate UI updates"""
        # CRITICAL: Direct connection for sub-10ms chunk latency
        self.websocket_client.chunk_received.connect(self._on_chunk_received)
        self.websocket_client.message_started.connect(self._on_message_started)
        self.websocket_client.message_completed.connect(self._on_message_completed)

        self.websocket_client.connection_status_changed.connect(
            self._on_connection_status_changed
        )
        self.websocket_client.error_occurred.connect(self._on_error)

        # Provider detection for automatic optimizations
        self.websocket_client.provider_detected.connect(self._on_provider_detected)

    def _setup_theme_signals(self) -> None:
        """Connect theme manager signals for real-time theme updates"""
        self.theme_manager.theme_mode_changed.connect(self._on_theme_changed)

    def _setup_header_icons(self, header_layout: QHBoxLayout) -> None:
        """Setup Material Design icons in the header"""
        # Theme toggle icon button
        if self.theme_manager.current_mode == ThemeMode.LIGHT:
            theme_icon_path = ":/icons/dark_mode.svg"
            theme_tooltip = "Switch to Dark Mode"
        else:
            theme_icon_path = ":/icons/light_mode.svg"
            theme_tooltip = "Switch to Light Mode"

        self.theme_icon_button = MaterialIconButton(
            icon_resource_path=theme_icon_path, size=24, tooltip=theme_tooltip
        )
        self.theme_icon_button.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_icon_button)

        # Settings icon button
        self.settings_icon_button = MaterialIconButton(
            icon_resource_path=":/icons/settings.svg",
            size=24,
            tooltip="Settings",
        )
        self.settings_icon_button.clicked.connect(self._open_settings)
        header_layout.addWidget(self.settings_icon_button)

    def _update_icon_themes(self) -> None:
        """Update all icon button themes"""
        current_config = self.theme_manager.current_config

        # Update theme toggle icon
        if hasattr(self, "theme_icon_button"):
            self.theme_icon_button.update_theme(current_config)
            # Update icon path and tooltip based on current theme
            if self.theme_manager.current_mode == ThemeMode.LIGHT:
                self.theme_icon_button._icon_resource_path = ":/icons/dark_mode.svg"
                self.theme_icon_button.setToolTip("Switch to Dark Mode")
            else:
                self.theme_icon_button._icon_resource_path = ":/icons/light_mode.svg"
                self.theme_icon_button.setToolTip("Switch to Light Mode")
            self.theme_icon_button.update_theme(current_config)  # Refresh with new path

        # Update settings icon
        if hasattr(self, "settings_icon_button"):
            self.settings_icon_button.update_theme(current_config)

        # Update send icon
        if hasattr(self, "send_icon_button"):
            self.send_icon_button.update_theme(current_config)

    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes"""
        self.theme_manager.toggle_theme()

        self.logger.info(
            "Theme toggled by user",
            theme_event="user_theme_toggle",
            module=__name__,
            new_theme=self.theme_manager.current_mode.value,
        )

    def _update_theme_toggle_button(self) -> None:
        """Update theme toggle button text based on current theme"""
        if self.theme_manager.current_mode == ThemeMode.LIGHT:
            self.theme_icon_button.setToolTip("🌙 Dark Mode")
        else:
            self.theme_icon_button.setToolTip("☀️ Light Mode")

    def _on_theme_changed(self, theme_mode: ThemeMode) -> None:
        """Handle theme change events"""
        # Update icon themes
        self._update_icon_themes()

        self.logger.info(
            "Theme changed in UI",
            theme_event="ui_theme_changed",
            module=__name__,
            theme_mode=theme_mode.value,
        )

    def _on_message_started(self, message_id: str, user_message: str) -> None:
        """
        Handle message start - prepare for streaming with markdown support.

        This is Phase 1 of the three-phase streaming protocol.
        """
        self._current_message_id = message_id
        self._is_streaming = True
        self._streaming_content = ""  # Reset content buffer

        # Get current model info for display
        provider_info = self.websocket_client.get_provider_info()
        model_name = provider_info.get("model", "Assistant")

        # Use full model name without truncation
        model_display = model_name or "Assistant"

        # Add assistant response header with model name
        header_html = f"<br><strong>🤖 {model_display}:</strong><br>"
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(header_html)

        # Store position for content updates
        self._current_message_start = self.chat_display.textCursor().position()

        self.logger.info(
            "Message streaming started",
            stream_event="message_start_ui",
            module=__name__,
            message_id=message_id,
        )

    def _on_chunk_received(self, chunk: str) -> None:
        """
        Handle incoming text chunk - accumulate for markdown processing.

        This is Phase 2 of the three-phase streaming protocol.
        For markdown support, we accumulate chunks and periodically render.
        """
        if self._is_streaming:
            # Accumulate content for markdown processing
            self._streaming_content += chunk

            # Render markdown every few words for responsive display
            # This balances performance with visual feedback
            if len(self._streaming_content.split()) % 5 == 0 or chunk.endswith(
                ("\n", ".", "!", "?")
            ):
                self._update_streaming_display()

    def _update_streaming_display(self) -> None:
        """Update the chat display with current markdown content."""
        if not self._streaming_content:
            return

        # Convert markdown to HTML
        html_content = self.markdown_formatter.format_message(self._streaming_content)

        # Replace content from the message start position
        cursor = self.chat_display.textCursor()
        cursor.setPosition(self._current_message_start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.insertHtml(html_content)

        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_message_completed(self, message_id: str, full_content: str) -> None:
        """
        Handle message completion with final markdown rendering.

        This is Phase 3 of the three-phase streaming protocol.
        """
        self._is_streaming = False
        self._current_message_id = None

        # Ensure final content is rendered with complete markdown
        if self._streaming_content:
            self._update_streaming_display()

        # Clear the content buffer
        self._streaming_content = ""

        self.logger.info(
            "Message streaming completed",
            stream_event="message_complete_ui",
            module=__name__,
            message_id=message_id,
            content_length=len(full_content),
        )

    def _on_connection_status_changed(self, is_connected: bool) -> None:
        """Update connection status indicator"""
        if is_connected:
            websocket_url = self.config_manager.get_websocket_url()
            self.status_label.setText(f"✅ Connected: {websocket_url}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.send_icon_button.setEnabled(True)
        else:
            active_profile = self.config_manager.get_active_backend_profile()
            if active_profile:
                self.status_label.setText(
                    f"❌ Disconnected from {active_profile.host}:{active_profile.port} - Click to retry"
                )
            else:
                self.status_label.setText("❌ No backend configured - Click to retry")
            self.status_label.setStyleSheet(
                "color: red; font-weight: bold; text-decoration: underline;"
            )
            self.send_icon_button.setEnabled(False)

    def _on_status_label_clicked(self, ev) -> None:
        """Handle status label click for manual reconnection"""
        if not self.websocket_client.is_connected:
            self.logger.info(
                "Manual reconnection requested",
                ui_event="manual_reconnection",
                module=__name__,
            )
            # Update status to show reconnection attempt
            self.status_label.setText("🔄 Reconnecting manually...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

            # Trigger manual reconnection
            self.websocket_client.connect_to_backend()

    def _on_error(self, error_message: str) -> None:
        """Handle WebSocket errors"""
        self.logger.error(
            "WebSocket error",
            ws_error_event="websocket_error",
            module=__name__,
            error=error_message,
        )
        self.chat_display.append(f"\n❌ Error: {error_message}")

        # If max retries exceeded, update status to show clickable retry option
        if "max retries exceeded" in error_message.lower():
            self._update_status_for_retry()

    def _update_status_for_retry(self) -> None:
        """Update status label to show clickable retry option after max attempts"""
        active_profile = self.config_manager.get_active_backend_profile()
        if active_profile:
            self.status_label.setText(
                f"❌ Disconnected from {active_profile.host}:{active_profile.port} - Click to retry"
            )
        else:
            self.status_label.setText("❌ No backend configured - Click to retry")
        self.status_label.setStyleSheet(
            "color: red; font-weight: bold; text-decoration: underline;"
        )

    def _on_provider_detected(
        self, provider: str, model: str, orchestrator: str
    ) -> None:
        """Handle provider detection and display optimization info"""
        self.logger.info(
            "Provider detected - optimizations applied",
            provider_event="provider_detected",
            module=__name__,
            provider=provider,
            model=model,
            orchestrator=orchestrator,
        )

        # Update status label to include provider info
        if self.websocket_client.is_connected:
            provider_summary = self.websocket_client.get_provider_summary()
            optimizations = provider_summary.get("optimizations", {})

            # Create a concise status message
            status_parts = [f"Connected ({provider}"]
            if model:
                # Use full model name without truncation
                status_parts.append(f" • {model}")
            status_parts.append(")")

            status_message = "".join(status_parts)
            self.status_label.setText(status_message)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

            # Log detailed optimization info
            self.logger.info(
                "Provider optimizations active",
                provider_event="optimizations_active",
                module=__name__,
                provider=provider,
                model=model,
                immediate_processing=optimizations.get("immediate_processing"),
                use_compression=optimizations.get("use_compression"),
                use_recoverable_errors=optimizations.get("use_recoverable_errors"),
                max_retries=optimizations.get("max_retries"),
            )

    def _open_settings(self) -> None:
        """Open the settings dialog"""
        settings_dialog = SettingsDialog(self)

        # Connect settings dialog signals
        settings_dialog.backend_changed.connect(self._on_backend_changed)
        settings_dialog.theme_changed.connect(self._on_settings_theme_changed)

        # Show dialog
        result = settings_dialog.exec()

        self.logger.info(
            "Settings dialog closed",
            ui_event="settings_dialog_closed",
            module=__name__,
            result="accepted" if result else "rejected",
        )

    def _on_backend_changed(self, profile_id: str) -> None:
        """Handle backend profile change from settings"""
        self.logger.info(
            "Backend changed from settings",
            config_event="backend_changed_from_settings",
            module=__name__,
            profile_id=profile_id,
        )

        # Update WebSocket URL and reconnect
        self.websocket_client.update_backend_url()

    def _on_settings_theme_changed(self, theme_name: str) -> None:
        """Handle theme change from settings"""
        self.logger.info(
            "Theme changed from settings",
            theme_event="theme_changed_from_settings",
            module=__name__,
            theme=theme_name,
        )
        # Theme change is handled automatically by the theme manager

    def _send_message(self) -> None:
        """Send user message and prepare for streaming response"""
        message = self.message_input.text().strip()
        if not message:
            return

        # Display user message with HTML formatting
        user_html = f"<br><strong>👤 You:</strong> {message}<br>"
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(user_html)

        # Send to WebSocket using correct protocol
        self.websocket_client.send_message(message)

        # Clear input and prepare for response
        self.message_input.clear()
        self._is_streaming = False

        self.logger.info(
            "Message sent",
            send_event="user_message_sent",
            module=__name__,
            message_length=len(message),
        )

    def resizeEvent(self, event: Any) -> None:
        """Handle window resize events and save geometry"""
        super().resizeEvent(event)

        # Save current window geometry to configuration
        geometry = self.geometry()
        self.config_manager.set_window_geometry(
            geometry.width(), geometry.height(), geometry.x(), geometry.y()
        )

    def moveEvent(self, event: Any) -> None:
        """Handle window move events and save geometry"""
        super().moveEvent(event)

        # Save current window geometry to configuration
        geometry = self.geometry()
        self.config_manager.set_window_geometry(
            geometry.width(), geometry.height(), geometry.x(), geometry.y()
        )

    def closeEvent(self, event: Any) -> None:
        """Clean shutdown"""
        self.logger.info(
            "Shutting down main window",
            shutdown_event="main_window_shutdown",
            module=__name__,
        )

        # Save final window geometry before closing
        geometry = self.geometry()
        self.config_manager.set_window_geometry(
            geometry.width(), geometry.height(), geometry.x(), geometry.y()
        )

        self.websocket_client.cleanup()
        event.accept()


# Export only the main controller class per PROJECT_RULES.md
__all__ = ["MainWindowController"]
