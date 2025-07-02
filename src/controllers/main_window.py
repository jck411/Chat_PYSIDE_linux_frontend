"""
Main Window Controller for Lightning-Fast Chat Streaming

Following PROJECT_RULES.md:
- ≤ 150 LOC with ≤ 2 public symbols per UI controller
- Keep UI thread under 10ms per frame
- Immediate chunk processing without batching delays
- Structured logging with performance tracking
"""

import structlog
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTextEdit,
    QLineEdit,
    QLabel,
)
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt

from .websocket_client import OptimizedWebSocketClient
from ..config import get_backend_config
from ..themes import get_theme_manager, ThemeMode, MaterialIconButton

# Import compiled resources
try:
    from .. import resources_rc  # type: ignore
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

    def __init__(self):
        super().__init__()
        self.logger = structlog.get_logger(__name__)

        # Get backend configuration
        self.backend_config = get_backend_config()

        # Initialize theme manager
        self.theme_manager = get_theme_manager()
        self._setup_theme_signals()

        # Initialize WebSocket client
        self.websocket_client = OptimizedWebSocketClient()
        self._setup_websocket_signals()

        # UI state for streaming
        self._current_message_start = 0
        self._is_streaming = False
        self._current_message_id = None

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
            backend_config=str(self.backend_config),
            theme_info=self.theme_manager.get_theme_info(),
        )

    def _setup_ui(self) -> None:
        """Setup minimal, fast UI for chat streaming"""
        self.setWindowTitle("Chat PySide Frontend - Lightning Fast Streaming")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header area with backend info and icons
        header_layout = QHBoxLayout()

        # Left side: Backend info
        backend_info = QLabel(f"Backend: {self.backend_config.websocket_url}")
        backend_info.setStyleSheet("color: #888888; font-size: 10px; padding: 5px;")
        header_layout.addWidget(backend_info)

        # Spacer to push icons to the right
        header_layout.addStretch()

        # Right side: Material Design icons
        self._setup_header_icons(header_layout)

        layout.addLayout(header_layout)

        # Connection status
        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Chat display - optimized for streaming
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
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
        self.websocket_client.connection_established.connect(
            self._on_connection_established
        )
        self.websocket_client.connection_status_changed.connect(
            self._on_connection_status_changed
        )
        self.websocket_client.error_occurred.connect(self._on_error)

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

        # Settings icon button (inactive for now)
        self.settings_icon_button = MaterialIconButton(
            icon_resource_path=":/icons/settings.svg",
            size=24,
            tooltip="Settings (Coming Soon)",
        )
        self.settings_icon_button.setEnabled(False)  # Inactive as requested
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

    def _on_connection_established(self, client_id: str) -> None:
        """Handle connection established with client ID"""
        self.logger.info(
            "Connection established with client ID",
            connect_event="connection_established",
            module=__name__,
            client_id=client_id,
        )
        self.chat_display.append(f"\n🔗 Connected with ID: {client_id}")

    def _on_message_started(self, message_id: str, user_message: str) -> None:
        """
        Handle message start - prepare for streaming.

        This is Phase 1 of the three-phase streaming protocol.
        """
        self._current_message_id = message_id
        self._is_streaming = True

        # Add assistant response header
        self.chat_display.append(f"\n🤖 Assistant (ID: {message_id[:8]}...):")
        self._current_message_start = self.chat_display.textCursor().position()

        self.logger.info(
            "Message streaming started",
            stream_event="message_start_ui",
            module=__name__,
            message_id=message_id,
        )

    def _on_chunk_received(self, chunk: str) -> None:
        """
        Handle incoming text chunk with immediate UI update.

        This is Phase 2 of the three-phase streaming protocol.
        OPTIMIZATION: Direct append without batching delays.
        This is the critical path for streaming performance.
        """
        if self._is_streaming:
            # Direct text append for immediate display
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(chunk)

            # Auto-scroll to bottom (optimized)
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _on_message_completed(self, message_id: str, full_content: str) -> None:
        """
        Handle message completion.

        This is Phase 3 of the three-phase streaming protocol.
        """
        self._is_streaming = False
        self._current_message_id = None

        self.logger.info(
            "Message streaming completed",
            stream_event="message_complete_ui",
            module=__name__,
            message_id=message_id,
            content_length=len(full_content),
        )

        # Add completion indicator
        self.chat_display.append(f"\n✅ Message completed (ID: {message_id[:8]}...)")

    def _on_connection_status_changed(self, is_connected: bool) -> None:
        """Update connection status indicator"""
        if is_connected:
            self.status_label.setText(
                f"✅ Connected to {self.backend_config.host}:{self.backend_config.port} - Ready for streaming"
            )
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.send_icon_button.setEnabled(True)
        else:
            self.status_label.setText(
                f"❌ Disconnected from {self.backend_config.host}:{self.backend_config.port} - Reconnecting..."
            )
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.send_icon_button.setEnabled(False)

    def _on_error(self, error_message: str) -> None:
        """Handle WebSocket errors"""
        self.logger.error(
            "WebSocket error",
            ws_error_event="websocket_error",
            module=__name__,
            error=error_message,
        )
        self.chat_display.append(f"\n❌ Error: {error_message}")

    def _send_message(self) -> None:
        """Send user message and prepare for streaming response"""
        message = self.message_input.text().strip()
        if not message:
            return

        # Display user message
        self.chat_display.append(f"\n👤 You: {message}")

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

    def closeEvent(self, event) -> None:
        """Clean shutdown"""
        self.logger.info(
            "Shutting down main window",
            shutdown_event="main_window_shutdown",
            module=__name__,
        )
        self.websocket_client.cleanup()
        event.accept()


# Export only the main controller class per PROJECT_RULES.md
__all__ = ["MainWindowController"]
