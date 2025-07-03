"""Tests for the main application module."""

from unittest.mock import MagicMock, patch

import pytest

from src.app import main, parse_args, setup_exception_handler, setup_logging


class TestSetupLogging:
    """Test logging configuration."""

    def test_setup_logging_configures_structlog(self):
        """Test that setup_logging configures structlog properly."""
        # This should not raise any exceptions
        setup_logging()

        # Verify we can get a logger
        import structlog

        logger = structlog.get_logger("test")
        assert logger is not None


class TestSetupExceptionHandler:
    """Test exception handler setup."""

    def test_setup_exception_handler_installs_hook(self):
        """Test that exception handler is installed."""
        import sys

        original_hook = sys.excepthook

        setup_exception_handler()

        # Verify the hook was changed
        assert sys.excepthook != original_hook

        # Restore original hook
        sys.excepthook = original_hook


class TestParseArgs:
    """Test command line argument parsing."""

    def test_parse_args_default(self):
        """Test parsing with no arguments."""
        with patch("sys.argv", ["app.py"]):
            args = parse_args()
            assert args.host is None
            assert args.port is None
            assert args.ssl is False

    def test_parse_args_with_host(self):
        """Test parsing with host argument."""
        with patch("sys.argv", ["app.py", "--host", "localhost"]):
            args = parse_args()
            assert args.host == "localhost"

    def test_parse_args_with_port(self):
        """Test parsing with port argument."""
        with patch("sys.argv", ["app.py", "--port", "9000"]):
            args = parse_args()
            assert args.port == 9000

    def test_parse_args_with_ssl(self):
        """Test parsing with SSL flag."""
        with patch("sys.argv", ["app.py", "--ssl"]):
            args = parse_args()
            assert args.ssl is True


class TestMain:
    """Test main application function."""

    @patch("src.app.MainWindowController")
    @patch("src.app.QApplication")
    @patch("qasync.QEventLoop")
    def test_main_creates_application(
        self, mock_event_loop, mock_qapp, mock_controller
    ):
        """Test that main creates QApplication and controller."""
        # Mock QApplication instance
        mock_app_instance = MagicMock()
        mock_qapp.return_value = mock_app_instance

        # Mock event loop
        mock_loop_instance = MagicMock()
        mock_loop_instance.__enter__ = MagicMock(return_value=mock_loop_instance)
        mock_loop_instance.__exit__ = MagicMock(return_value=None)
        # Make run_forever raise an exception to exit the function
        mock_loop_instance.run_forever.side_effect = KeyboardInterrupt("Test exit")
        mock_event_loop.return_value = mock_loop_instance

        # Mock controller
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance

        with patch("sys.argv", ["app.py"]):
            with patch("asyncio.set_event_loop"):
                with pytest.raises(KeyboardInterrupt):  # Expected from our mock
                    main()

        # Verify QApplication was created
        mock_qapp.assert_called_once()

        # Verify controller was created and shown
        mock_controller.assert_called_once()
        mock_controller_instance.show.assert_called_once()

        # Verify event loop was set up
        mock_event_loop.assert_called_once_with(mock_app_instance)
        mock_loop_instance.run_forever.assert_called_once()
