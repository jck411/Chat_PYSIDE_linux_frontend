#!/usr/bin/env python3
"""
Chat PySide Frontend - Main Application Entry Point

Following PROJECT_RULES.md:
- Python 3.13.0 + PySide6 6.8.1.1
- qasync for Qt + asyncio integration
- Structured logging with structlog
- Global exception handling
- Async-first design for WebSocket streaming
"""

import sys
import asyncio
import argparse
import structlog
from PySide6.QtWidgets import QApplication
import qasync  # type: ignore

try:
    # Try relative imports first (when run as module)
    from .controllers.main_window import MainWindowController
    from .config import get_config_manager
except ImportError:
    # Fall back to absolute imports (when run directly)
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.controllers.main_window import MainWindowController
    from src.config import get_config_manager


def setup_logging() -> None:
    """Configure structured JSON logging per PROJECT_RULES.md"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_exception_handler() -> None:
    """Install global exception hook per PROJECT_RULES.md"""
    logger = structlog.get_logger(__name__)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "Uncaught exception",
            exception_event="global_exception",
            module=__name__,
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PySide6 chat frontend with WebSocket streaming"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Backend host address (default: from env or 192.168.1.223)",
    )
    parser.add_argument(
        "--port", type=int, help="Backend port number (default: from env or 8000)"
    )
    parser.add_argument(
        "--ssl", action="store_true", help="Use SSL/TLS (wss:// and https://)"
    )
    return parser.parse_args()


def main() -> None:
    """Main application entry point"""
    setup_logging()
    setup_exception_handler()

    # Parse command line arguments
    args = parse_args()

    # Get configuration manager
    config_manager = get_config_manager()

    # Update configuration if arguments provided
    if args.host or args.port or args.ssl:
        # Create a temporary backend profile for command line args
        profile_name = "Command Line Override"
        active_profile = config_manager.get_active_backend_profile()
        if active_profile:
            host = args.host or active_profile.host
            port = args.port or active_profile.port
            use_ssl = args.ssl if args.ssl else active_profile.use_ssl
        else:
            host = args.host or "localhost"
            port = args.port or 8000
            use_ssl = args.ssl or False

        config_manager.add_backend_profile(
            "cli_override",
            profile_name,
            host,
            port,
            use_ssl,
            "Temporary profile from command line arguments",
        )
        config_manager.set_active_backend("cli_override")

    logger = structlog.get_logger(__name__)
    logger.info(
        "Starting Chat PySide Frontend",
        app_event="app_start",
        module=__name__,
        backend_url=config_manager.get_websocket_url(),
    )

    # Create QApplication (filter out our custom args)
    qt_args = [
        arg for arg in sys.argv if not arg.startswith(("--host", "--port", "--ssl"))
    ]
    app = QApplication(qt_args)

    # Set up qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    logger.info(
        "QApplication and qasync event loop created",
        app_event="qapp_created",
        module=__name__,
    )

    # Create and show main window
    main_controller = MainWindowController()
    main_controller.show()

    # Run the application
    with loop:
        loop.run_forever()


def run_app():
    """Entry point for the application"""
    try:
        main()
    except RuntimeError as e:
        if "QApplication" in str(e):
            print(
                "Note: QApplication singleton issue detected. Try restarting the terminal."
            )
            print("This can happen when running the app multiple times quickly.")
            print(f"Error: {e}")
        else:
            raise
    except Exception as e:
        print(f"Application error: {e}")
        raise


if __name__ == "__main__":
    run_app()
