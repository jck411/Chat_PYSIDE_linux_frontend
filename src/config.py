"""
Configuration Management for Chat Frontend

Following PROJECT_RULES.md:
- Read secrets via os.getenv
- Fail-fast validation
- Single responsibility
- Structured logging integration
"""

import os
import structlog
from typing import Optional


class BackendConfig:
    """
    Backend connection configuration with environment variable support.
    
    Supports both environment variables and direct configuration.
    Validates connection parameters on initialization.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        use_ssl: Optional[bool] = None
    ):
        self.logger = structlog.get_logger(__name__)
        
        # Read from environment variables with fallbacks
        self.host = host or os.getenv("CHAT_BACKEND_HOST", "192.168.1.223")
        self.port = port or int(os.getenv("CHAT_BACKEND_PORT", "8000"))
        self.use_ssl = use_ssl if use_ssl is not None else os.getenv("CHAT_BACKEND_SSL", "false").lower() == "true"
        
        # Validate configuration
        self._validate()
        
        self.logger.info(
            "Backend configuration loaded",
            config_event="config_loaded",
            module=__name__,
            host=self.host,
            port=self.port,
            use_ssl=self.use_ssl
        )
    
    def _validate(self) -> None:
        """Validate configuration parameters - fail fast per PROJECT_RULES.md"""
        if not self.host:
            raise ValueError("Backend host cannot be empty")
        
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port number: {self.port}. Must be 1-65535")
        
        if not isinstance(self.use_ssl, bool):
            raise TypeError(f"use_ssl must be boolean, got {type(self.use_ssl)}")
    
    @property
    def websocket_url(self) -> str:
        """Get the complete WebSocket URL"""
        protocol = "wss" if self.use_ssl else "ws"
        return f"{protocol}://{self.host}:{self.port}/ws/chat"
    
    @property
    def health_url(self) -> str:
        """Get the health check URL"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}/health"
    
    @property
    def base_url(self) -> str:
        """Get the base backend URL"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    def __str__(self) -> str:
        """String representation for logging"""
        return f"BackendConfig(host={self.host}, port={self.port}, ssl={self.use_ssl})"


# Global configuration instance
# Can be overridden by importing modules if needed
backend_config = BackendConfig()


def get_backend_config() -> BackendConfig:
    """Get the current backend configuration"""
    return backend_config


def set_backend_config(
    host: Optional[str] = None,
    port: Optional[int] = None,
    use_ssl: Optional[bool] = None
) -> BackendConfig:
    """
    Update the global backend configuration.
    
    Args:
        host: Backend host address
        port: Backend port number
        use_ssl: Whether to use SSL/TLS
    
    Returns:
        Updated BackendConfig instance
    """
    global backend_config
    backend_config = BackendConfig(host=host, port=port, use_ssl=use_ssl)
    return backend_config


# Export only necessary symbols per PROJECT_RULES.md
__all__ = ["BackendConfig", "get_backend_config", "set_backend_config"] 