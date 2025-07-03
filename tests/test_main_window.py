"""Tests for the main window controller."""

from unittest.mock import MagicMock, patch

import pytest

from src.controllers.main_window import MainWindowController


class TestMainWindowController:
    """Test MainWindowController class."""

    @pytest.fixture
    def mock_websocket_client(self):
        """Create a mock WebSocket client."""
        with patch(
            "src.controllers.main_window.OptimizedWebSocketClient"
        ) as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def main_window(self, qapp, mock_websocket_client):
        """Create a MainWindowController instance for testing."""
        window = MainWindowController()
        yield window
        window.close()

    def test_main_window_initialization(self, main_window, mock_websocket_client):
        """Test that main window initializes correctly."""
        assert main_window.windowTitle() == "Chat PySide Frontend"
        assert main_window.websocket_client is not None

        # Verify WebSocket client was set up
        mock_websocket_client.connect_to_backend.assert_called_once()

    def test_ui_components_exist(self, main_window):
        """Test that all UI components are created."""
        assert hasattr(main_window, "chat_display")
        assert hasattr(main_window, "message_input")
        assert hasattr(main_window, "send_icon_button")
        assert hasattr(main_window, "status_label")

        # Verify components are properly configured
        assert main_window.chat_display.isReadOnly()
        assert main_window.message_input.placeholderText() == "Type your message..."

    def test_websocket_signals_connected(self, main_window, mock_websocket_client):
        """Test that WebSocket signals are properly connected."""
        # Verify connect calls were made
        mock_websocket_client.chunk_received.connect.assert_called()
        mock_websocket_client.message_started.connect.assert_called()
        mock_websocket_client.message_completed.connect.assert_called()
        mock_websocket_client.connection_established.connect.assert_called()
        mock_websocket_client.connection_status_changed.connect.assert_called()
        mock_websocket_client.error_occurred.connect.assert_called()

    def test_send_message_with_text(self, main_window, mock_websocket_client):
        """Test sending a message with text."""
        test_message = "Hello, world!"
        main_window.message_input.setText(test_message)

        # Trigger send message
        main_window._send_message()

        # Verify message was sent to WebSocket client
        mock_websocket_client.send_message.assert_called_once_with(test_message)

        # Verify input was cleared
        assert main_window.message_input.text() == ""

    def test_send_message_empty_text(self, main_window, mock_websocket_client):
        """Test sending an empty message (should be ignored)."""
        main_window.message_input.setText("")

        # Trigger send message
        main_window._send_message()

        # Verify no message was sent
        mock_websocket_client.send_message.assert_not_called()

    def test_send_message_whitespace_only(self, main_window, mock_websocket_client):
        """Test sending whitespace-only message (should be ignored)."""
        main_window.message_input.setText("   \n\t   ")

        # Trigger send message
        main_window._send_message()

        # Verify no message was sent
        mock_websocket_client.send_message.assert_not_called()

    def test_on_connection_established(self, main_window):
        """Test connection established handler."""
        test_client_id = "test-client-123"

        # Trigger connection established
        main_window._on_connection_established(test_client_id)

        # Verify message was added to chat display
        chat_text = main_window.chat_display.toPlainText()
        assert test_client_id in chat_text
        assert "Connected with ID" in chat_text

    def test_on_message_started(self, main_window):
        """Test message started handler."""
        test_message_id = "msg-123"
        test_user_message = "Test message"

        # Trigger message started
        main_window._on_message_started(test_message_id, test_user_message)

        # Verify streaming state is set
        assert main_window._is_streaming is True
        assert main_window._current_message_id == test_message_id

        # Verify assistant header was added
        chat_text = main_window.chat_display.toPlainText()
        assert "Assistant" in chat_text
        assert test_message_id[:8] in chat_text

    def test_on_chunk_received_while_streaming(self, main_window):
        """Test chunk received handler while streaming."""
        # Set up streaming state
        main_window._is_streaming = True

        test_chunk = "This is a test chunk"

        # Trigger chunk received
        main_window._on_chunk_received(test_chunk)

        # Verify chunk was added to chat display
        chat_text = main_window.chat_display.toPlainText()
        assert test_chunk in chat_text

    def test_on_chunk_received_not_streaming(self, main_window):
        """Test chunk received handler when not streaming."""
        # Ensure not streaming
        main_window._is_streaming = False

        initial_text = main_window.chat_display.toPlainText()
        test_chunk = "This chunk should be ignored"

        # Trigger chunk received
        main_window._on_chunk_received(test_chunk)

        # Verify chunk was not added
        final_text = main_window.chat_display.toPlainText()
        assert final_text == initial_text
        assert test_chunk not in final_text

    def test_on_message_completed(self, main_window):
        """Test message completed handler."""
        # Set up streaming state
        main_window._is_streaming = True
        main_window._current_message_id = "msg-123"

        test_message_id = "msg-123"
        test_content = "Complete message content"

        # Trigger message completed
        main_window._on_message_completed(test_message_id, test_content)

        # Verify streaming state is cleared
        assert main_window._is_streaming is False
        assert main_window._current_message_id is None

        # Verify completion message was added
        chat_text = main_window.chat_display.toPlainText()
        assert "Message completed" in chat_text

    def test_on_connection_status_changed_connected(self, main_window):
        """Test connection status change to connected."""
        main_window._on_connection_status_changed(True)

        # Verify status label shows connected
        status_text = main_window.status_label.text()
        assert "Connected" in status_text

        # Verify send button is enabled
        assert main_window.send_icon_button.isEnabled()

    def test_on_connection_status_changed_disconnected(self, main_window):
        """Test connection status change to disconnected."""
        main_window._on_connection_status_changed(False)

        # Verify status label shows disconnected
        status_text = main_window.status_label.text()
        assert "Disconnected" in status_text

        # Verify send button is disabled
        assert not main_window.send_icon_button.isEnabled()

    def test_on_error(self, main_window):
        """Test error handler."""
        test_error = "Test error message"

        main_window._on_error(test_error)

        # Verify error was added to chat display
        chat_text = main_window.chat_display.toPlainText()
        assert test_error in chat_text
        assert "Error:" in chat_text

    def test_close_event_cleanup(self, main_window, mock_websocket_client):
        """Test that close event triggers cleanup."""
        from PySide6.QtGui import QCloseEvent

        close_event = QCloseEvent()

        # Trigger close event
        main_window.closeEvent(close_event)

        # Verify WebSocket client cleanup was called
        mock_websocket_client.cleanup.assert_called_once()

        # Verify event was accepted
        assert close_event.isAccepted()
