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
    QPushButton,
    QLabel,
)
from PySide6.QtGui import QFont, QTextCursor

from .websocket_client import OptimizedWebSocketClient
from ..config import get_backend_config


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

        # Initialize WebSocket client
        self.websocket_client = OptimizedWebSocketClient()
        self._setup_websocket_signals()

        # UI state for streaming
        self._current_message_start = 0
        self._is_streaming = False
        self._current_message_id = None

        # Setup UI
        self._setup_ui()

        # Auto-connect on startup
        self.websocket_client.connect_to_backend()

        self.logger.info(
            "Main window initialized",
            window_event="main_window_init",
            module=__name__,
            backend_config=str(self.backend_config),
        )

    def _setup_ui(self) -> None:
        """Setup minimal, fast UI for chat streaming"""
        self.setWindowTitle("Chat PySide Frontend - Lightning Fast Streaming")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Backend info
        backend_info = QLabel(f"Backend: {self.backend_config.websocket_url}")
        backend_info.setStyleSheet("color: #888888; font-size: 10px; padding: 5px;")
        layout.addWidget(backend_info)

        # Connection status
        self.status_label = QLabel("Connecting...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Chat display - optimized for streaming
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        self.chat_display.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
                padding: 10px;
            }
        """
        )
        layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

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
            self.send_button.setEnabled(True)
        else:
            self.status_label.setText(
                f"❌ Disconnected from {self.backend_config.host}:{self.backend_config.port} - Reconnecting..."
            )
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.send_button.setEnabled(False)

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
