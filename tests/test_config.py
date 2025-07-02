"""Tests for the configuration system."""

import os
from unittest.mock import patch

from src.config import (
    get_config_manager,
    ThemePreference,
    BackendProfile,
    EnvConfig,
)


class TestEnvConfig:
    """Test environment configuration."""

    def test_env_config_creation(self):
        """Test creating an EnvConfig instance."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert config.speechgram_api_key is None

    def test_env_config_with_api_key(self):
        """Test loading API key from environment."""
        env_vars = {"SPEECHGRAM_API_KEY": "test-key"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = EnvConfig()
            assert config.speechgram_api_key == "test-key"

    def test_has_speechgram_api_key(self):
        """Test checking for API key presence."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvConfig()
            assert not config.has_speechgram_api_key()

        with patch.dict(os.environ, {"SPEECHGRAM_API_KEY": "test-key"}, clear=True):
            config = EnvConfig()
            assert config.has_speechgram_api_key()


class TestBackendProfile:
    """Test backend profile functionality."""

    def test_backend_profile_creation(self):
        """Test creating a backend profile."""
        profile = BackendProfile(
            name="Test Profile",
            host="localhost",
            port=8000,
            use_ssl=False,
            description="Test description",
        )

        assert profile.name == "Test Profile"
        assert profile.host == "localhost"
        assert profile.port == 8000
        assert not profile.use_ssl
        assert profile.description == "Test description"

    def test_websocket_url_without_ssl(self):
        """Test WebSocket URL generation without SSL."""
        profile = BackendProfile(
            name="Test", host="example.com", port=8000, use_ssl=False, description=""
        )

        assert profile.websocket_url == "ws://example.com:8000/ws/chat"

    def test_websocket_url_with_ssl(self):
        """Test WebSocket URL generation with SSL."""
        profile = BackendProfile(
            name="Test", host="example.com", port=8443, use_ssl=True, description=""
        )

        assert profile.websocket_url == "wss://example.com:8443/ws/chat"

    def test_health_url_without_ssl(self):
        """Test health URL generation without SSL."""
        profile = BackendProfile(
            name="Test", host="example.com", port=8000, use_ssl=False, description=""
        )

        assert profile.health_url == "http://example.com:8000/health"

    def test_health_url_with_ssl(self):
        """Test health URL generation with SSL."""
        profile = BackendProfile(
            name="Test", host="example.com", port=8443, use_ssl=True, description=""
        )

        assert profile.health_url == "https://example.com:8443/health"


class TestConfigManagerSingleton:
    """Test the config manager singleton."""

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns the same instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2

    def test_config_manager_basic_functionality(self):
        """Test basic config manager functionality."""
        manager = get_config_manager()

        # Test that we can get basic configuration
        assert manager.get_theme_preference() in [
            ThemePreference.LIGHT,
            ThemePreference.DARK,
            ThemePreference.SYSTEM,
        ]

        # Test that we can get backend profile
        profile = manager.get_active_backend_profile()
        assert profile is not None
        assert hasattr(profile, "host")
        assert hasattr(profile, "port")
        assert hasattr(profile, "use_ssl")

        # Test that we can get websocket URL
        url = manager.get_websocket_url()
        assert url.startswith(("ws://", "wss://"))
        assert "/ws/chat" in url
