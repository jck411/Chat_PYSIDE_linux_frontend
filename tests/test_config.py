"""Tests for the configuration module."""

import os
import pytest
from unittest.mock import patch

from src.config import BackendConfig, get_backend_config, set_backend_config


class TestBackendConfig:
    """Test BackendConfig dataclass."""

    def test_backend_config_creation(self):
        """Test creating a BackendConfig instance."""
        config = BackendConfig(host="localhost", port=8080, use_ssl=True)

        assert config.host == "localhost"
        assert config.port == 8080
        assert config.use_ssl is True

    def test_websocket_url_without_ssl(self):
        """Test WebSocket URL generation without SSL."""
        config = BackendConfig(host="example.com", port=8000, use_ssl=False)

        assert config.websocket_url == "ws://example.com:8000/ws/chat"

    def test_websocket_url_with_ssl(self):
        """Test WebSocket URL generation with SSL."""
        config = BackendConfig(host="example.com", port=8443, use_ssl=True)

        assert config.websocket_url == "wss://example.com:8443/ws/chat"

    def test_health_url_without_ssl(self):
        """Test health URL generation without SSL."""
        config = BackendConfig(host="example.com", port=8000, use_ssl=False)

        assert config.health_url == "http://example.com:8000/health"

    def test_health_url_with_ssl(self):
        """Test health URL generation with SSL."""
        config = BackendConfig(host="example.com", port=8443, use_ssl=True)

        assert config.health_url == "https://example.com:8443/health"

    def test_base_url_without_ssl(self):
        """Test base URL generation without SSL."""
        config = BackendConfig(host="example.com", port=8000, use_ssl=False)

        assert config.base_url == "http://example.com:8000"

    def test_base_url_with_ssl(self):
        """Test base URL generation with SSL."""
        config = BackendConfig(host="example.com", port=8443, use_ssl=True)

        assert config.base_url == "https://example.com:8443"

    def test_config_validation_empty_host(self):
        """Test validation fails with empty host."""
        with patch.dict(os.environ, {"CHAT_BACKEND_HOST": ""}, clear=True):
            with pytest.raises(ValueError, match="Backend host cannot be empty"):
                BackendConfig(host="", port=8000, use_ssl=False)

    def test_config_validation_invalid_port(self):
        """Test validation fails with invalid port."""
        with pytest.raises(ValueError, match="Invalid port number"):
            BackendConfig(host="example.com", port=70000, use_ssl=False)

    def test_config_validation_negative_port(self):
        """Test validation fails with negative port."""
        with pytest.raises(ValueError, match="Invalid port number"):
            BackendConfig(host="example.com", port=-1, use_ssl=False)


class TestGetBackendConfig:
    """Test get_backend_config function."""

    def test_get_backend_config_default(self):
        """Test getting default configuration."""
        with patch.dict(os.environ, {}, clear=True):
            config = BackendConfig()  # Create fresh instance

            assert config.host == "192.168.1.223"
            assert config.port == 8000
            assert config.use_ssl is False

    def test_get_backend_config_from_env(self):
        """Test getting configuration from environment variables."""
        env_vars = {
            "CHAT_BACKEND_HOST": "test.example.com",
            "CHAT_BACKEND_PORT": "9000",
            "CHAT_BACKEND_SSL": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = BackendConfig()

            assert config.host == "test.example.com"
            assert config.port == 9000
            assert config.use_ssl is True

    def test_get_backend_config_ssl_false_values(self):
        """Test SSL configuration with various false values."""
        false_values = ["false", "False", "FALSE", "0", "no", ""]

        for false_value in false_values:
            with patch.dict(os.environ, {"CHAT_BACKEND_SSL": false_value}, clear=True):
                config = BackendConfig()
                assert config.use_ssl is False, f"Failed for value: {false_value}"

    def test_get_backend_config_invalid_port_env(self):
        """Test handling of invalid port values from environment."""
        with patch.dict(os.environ, {"CHAT_BACKEND_PORT": "invalid"}, clear=True):
            # Should raise ValueError when trying to convert to int
            with pytest.raises(ValueError):
                BackendConfig()


class TestSetBackendConfig:
    """Test set_backend_config function."""

    def test_set_backend_config_all_params(self):
        """Test setting all configuration parameters."""
        config = set_backend_config(host="new.example.com", port=9999, use_ssl=True)

        assert config.host == "new.example.com"
        assert config.port == 9999
        assert config.use_ssl is True

        # Verify global config was updated
        global_config = get_backend_config()
        assert global_config.host == "new.example.com"
        assert global_config.port == 9999
        assert global_config.use_ssl is True

    def test_set_backend_config_partial_params(self):
        """Test setting only some configuration parameters."""
        # First set a baseline
        set_backend_config(host="baseline.com", port=8000, use_ssl=False)

        # Then update only host (others should use environment defaults)
        with patch.dict(
            os.environ,
            {
                "CHAT_BACKEND_HOST": "baseline.com",
                "CHAT_BACKEND_PORT": "8000",
                "CHAT_BACKEND_SSL": "false",
            },
            clear=True,
        ):
            config = set_backend_config(host="updated.com")

            assert config.host == "updated.com"
            assert config.port == 8000  # From environment
            assert config.use_ssl is False  # From environment

    def test_set_backend_config_none_values(self):
        """Test setting configuration with None values (should use environment)."""
        with patch.dict(
            os.environ,
            {
                "CHAT_BACKEND_HOST": "env.example.com",
                "CHAT_BACKEND_PORT": "7777",
                "CHAT_BACKEND_SSL": "true",
            },
            clear=True,
        ):
            config = set_backend_config(host=None, port=None, use_ssl=None)

            # Should use environment values
            assert config.host == "env.example.com"
            assert config.port == 7777
            assert config.use_ssl is True
