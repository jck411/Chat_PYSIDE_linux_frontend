"""
Provider Configuration and Optimization Settings

Handles provider-specific optimization settings for WebSocket streaming.
Following PROJECT_RULES.md:
- Fail-fast validation
- Structured logging
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog


class ProviderType(Enum):
    """Supported AI providers"""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    UNKNOWN = "unknown"


@dataclass
class ProviderOptimizations:
    """Provider-specific optimization settings"""

    # Chunk processing settings
    immediate_processing: bool = True
    chunk_buffer_size: int = 0

    # Compression settings
    use_compression: bool = True
    compression_level: str = "deflate"

    # Error handling settings
    use_recoverable_errors: bool = False
    retry_on_recoverable: bool = False
    max_retries: int = 3

    # Performance tuning
    ping_interval: int = 20
    ping_timeout: int = 10
    max_message_size: int = 2**20  # 1MB

    # Connection settings
    connection_pool_size: int = 1
    keep_alive: bool = True


class ProviderConfigManager:
    """
    Manages provider-specific configurations and optimizations.

    Automatically detects provider information from WebSocket messages
    and applies optimal settings for each provider.
    """

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)
        self._current_provider: ProviderType = ProviderType.UNKNOWN
        self._current_model: str | None = None
        self._current_orchestrator: str | None = None

        # Initialize provider-specific configurations first
        self._provider_configs = self._initialize_provider_configs()

        # Then initialize optimizations using the configs
        self._optimizations: ProviderOptimizations = self._get_default_optimizations()

    def _initialize_provider_configs(self) -> dict[ProviderType, ProviderOptimizations]:
        """Initialize provider-specific optimization configurations"""

        return {
            ProviderType.ANTHROPIC: ProviderOptimizations(
                # Anthropic optimizations
                immediate_processing=True,
                chunk_buffer_size=0,
                use_compression=True,
                compression_level="deflate",
                use_recoverable_errors=True,
                retry_on_recoverable=True,
                max_retries=5,
                ping_interval=15,  # Slightly more frequent for Anthropic
                ping_timeout=8,
                max_message_size=2**21,  # 2MB for larger Claude responses
                connection_pool_size=1,
                keep_alive=True,
            ),
            ProviderType.OPENAI: ProviderOptimizations(
                # OpenAI optimizations
                immediate_processing=True,
                chunk_buffer_size=0,
                use_compression=True,
                compression_level="deflate",
                use_recoverable_errors=False,
                retry_on_recoverable=False,
                max_retries=3,
                ping_interval=20,
                ping_timeout=10,
                max_message_size=2**20,  # 1MB standard
                connection_pool_size=1,
                keep_alive=True,
            ),
            ProviderType.UNKNOWN: ProviderOptimizations(
                # Conservative defaults for unknown providers
                immediate_processing=True,
                chunk_buffer_size=0,
                use_compression=True,
                compression_level="deflate",
                use_recoverable_errors=False,
                retry_on_recoverable=False,
                max_retries=3,
                ping_interval=30,
                ping_timeout=15,
                max_message_size=2**20,  # 1MB
                connection_pool_size=1,
                keep_alive=True,
            ),
        }

    def _get_default_optimizations(self) -> ProviderOptimizations:
        """Get default optimization settings"""
        return self._provider_configs.get(ProviderType.UNKNOWN, ProviderOptimizations())

    def update_provider_info(self, provider_info: dict[str, Any]) -> bool:
        """
        Update current provider information and apply optimizations.

        Args:
            provider_info: Provider information from WebSocket message

        Returns:
            True if provider changed and optimizations were updated
        """
        provider_name = provider_info.get("provider", "").lower()
        model = provider_info.get("model", "")
        orchestrator = provider_info.get("orchestrator_type", "")

        # Map provider name to enum
        if provider_name == "anthropic":
            new_provider = ProviderType.ANTHROPIC
        elif provider_name == "openai":
            new_provider = ProviderType.OPENAI
        else:
            new_provider = ProviderType.UNKNOWN

        # Check if provider changed
        provider_changed = (
            new_provider != self._current_provider
            or model != self._current_model
            or orchestrator != self._current_orchestrator
        )

        if provider_changed:
            old_provider = self._current_provider
            self._current_provider = new_provider
            self._current_model = model
            self._current_orchestrator = orchestrator

            # Update optimizations
            self._optimizations = self._provider_configs.get(
                new_provider, self._get_default_optimizations()
            )

            self.logger.info(
                "Provider configuration updated",
                provider_event="provider_changed",
                module=__name__,
                old_provider=old_provider.value if old_provider else None,
                new_provider=new_provider.value,
                model=model,
                orchestrator=orchestrator,
            )

            return True

        return False

    def get_current_provider(self) -> ProviderType:
        """Get the currently detected provider"""
        return self._current_provider

    def get_current_model(self) -> str | None:
        """Get the currently detected model"""
        return self._current_model

    def get_current_orchestrator(self) -> str | None:
        """Get the currently detected orchestrator"""
        return self._current_orchestrator

    def get_optimizations(self) -> ProviderOptimizations:
        """Get current optimization settings"""
        return self._optimizations

    def should_use_recoverable_errors(self) -> bool:
        """Check if recoverable error handling should be used"""
        return self._optimizations.use_recoverable_errors

    def should_retry_on_recoverable(self) -> bool:
        """Check if automatic retry on recoverable errors is enabled"""
        return self._optimizations.retry_on_recoverable

    def get_websocket_config(self) -> dict[str, Any]:
        """Get WebSocket connection configuration based on current provider"""
        return {
            "ping_interval": self._optimizations.ping_interval,
            "ping_timeout": self._optimizations.ping_timeout,
            "max_size": self._optimizations.max_message_size,
            "compression": self._optimizations.compression_level
            if self._optimizations.use_compression
            else None,
        }

    def get_provider_summary(self) -> dict[str, Any]:
        """Get current provider configuration summary"""
        return {
            "provider": self._current_provider.value,
            "model": self._current_model,
            "orchestrator": self._current_orchestrator,
            "optimizations": {
                "immediate_processing": self._optimizations.immediate_processing,
                "use_compression": self._optimizations.use_compression,
                "use_recoverable_errors": self._optimizations.use_recoverable_errors,
                "max_retries": self._optimizations.max_retries,
                "ping_interval": self._optimizations.ping_interval,
            },
        }


# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "ProviderConfigManager",
    "ProviderOptimizations",
    "ProviderType",
]
