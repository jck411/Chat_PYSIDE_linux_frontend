"""Pytest configuration and fixtures for the Chat PySide Frontend tests."""

import asyncio
from collections.abc import Generator

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create an event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication]:
    """Create a Qt application instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Ensure we have a QApplication instance
    assert isinstance(app, QApplication)
    yield app
