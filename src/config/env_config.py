"""
Environment Configuration Management

Handles API keys and secrets from environment variables.
Following PROJECT_RULES.md:
- Read secrets via os.getenv
- Fail-fast validation
- Never log actual key values
"""

import os
import structlog
from typing import Optional, Any
from pathlib import Path


class EnvConfig:
    """
    Environment configuration for API keys and secrets.

    Handles secure loading and validation of environment variables.
    Never logs actual key values per PROJECT_RULES.md security guidelines.
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

        # Load API keys from environment
        self.speechgram_api_key = os.getenv("SPEECHGRAM_API_KEY")

        # Optional config path override
        self.config_path_override = os.getenv("CHAT_CONFIG_PATH")

        # Log configuration status without exposing keys
        self.logger.info(
            "Environment configuration loaded",
            config_event="env_config_loaded",
            module=__name__,
            speechgram_key_present=bool(self.speechgram_api_key),
            config_path_override=bool(self.config_path_override),
        )

    def get_speechgram_api_key(self) -> Optional[str]:
        """
        Get Speechgram API key for Speech-to-Text functionality.

        Returns:
            API key if present, None otherwise
        """
        return self.speechgram_api_key

    def has_speechgram_api_key(self) -> bool:
        """Check if Speechgram API key is configured"""
        return self.speechgram_api_key is not None

    def get_config_path_override(self) -> Optional[Path]:
        """
        Get custom config file path if specified in environment.

        Returns:
            Path object if override specified, None otherwise
        """
        if self.config_path_override:
            return Path(self.config_path_override)
        return None

    def validate_required_keys(self, require_speechgram: bool = False) -> None:
        """
        Validate that required API keys are present - fail fast per PROJECT_RULES.md

        Args:
            require_speechgram: Whether Speechgram API key is required

        Raises:
            ValueError: If any required keys are missing
        """
        missing_keys = []

        if require_speechgram and not self.has_speechgram_api_key():
            missing_keys.append("SPEECHGRAM_API_KEY")

        if missing_keys:
            raise ValueError(f"Missing required API keys: {missing_keys}")

    def get_configured_services(self) -> list[str]:
        """Get list of services with configured API keys"""
        services = []
        if self.has_speechgram_api_key():
            services.append("speechgram")
        return services


# Global instance
_env_config: Optional[EnvConfig] = None


def get_env_config() -> EnvConfig:
    """Get the global environment configuration instance"""
    global _env_config
    if _env_config is None:
        _env_config = EnvConfig()
    return _env_config


def validate_environment(require_speechgram: bool = False) -> dict[str, Any]:
    """
    Validate environment configuration and return status report.

    Args:
        require_speechgram: Whether to require Speechgram API key

    Returns:
        Dictionary with validation results and recommendations
    """
    logger = structlog.get_logger(__name__)

    validation_results: dict[str, Any] = {
        "status": "valid",
        "issues": [],
        "recommendations": [],
    }

    try:
        env_config = get_env_config()

        # Validate required keys
        env_config.validate_required_keys(require_speechgram=require_speechgram)

        # Get configured services
        configured_services = env_config.get_configured_services()
        validation_results["configured_services"] = configured_services

        if not configured_services:
            validation_results["recommendations"].append(
                "No API keys configured. Add SPEECHGRAM_API_KEY to .env file when needed for STT functionality."
            )

        logger.info(
            "Environment validation completed",
            config_event="env_validated",
            module=__name__,
            **validation_results,
        )

    except Exception as e:
        validation_results["status"] = "invalid"
        validation_results["issues"].append(str(e))
        logger.error(
            "Environment validation failed",
            config_event="env_validation_failed",
            module=__name__,
            error=str(e),
        )

    return validation_results


# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "EnvConfig",
    "get_env_config",
    "validate_environment",
]
