"""
Backend Profile Management

Handles backend server configurations and profiles.
Following PROJECT_RULES.md:
- Fail-fast validation
- Structured logging
"""

import structlog
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class ConnectionType(Enum):
    """Connection type for backend profiles"""

    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"


@dataclass
class BackendProfile:
    """
    Backend server profile configuration.

    Represents a complete backend server configuration including
    connection details and metadata.
    """

    name: str
    host: str
    port: int
    use_ssl: bool
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate profile data after initialization"""
        self._validate()

    def _validate(self) -> None:
        """Validate profile configuration - fail fast per PROJECT_RULES.md"""
        if not self.name or not self.name.strip():
            raise ValueError("Profile name cannot be empty")

        if not self.host or not self.host.strip():
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackendProfile":
        """Create profile from dictionary (JSON deserialization)"""
        return cls(**data)

    def __str__(self) -> str:
        """String representation for logging"""
        return f"BackendProfile(name='{self.name}', host={self.host}, port={self.port}, ssl={self.use_ssl})"


class BackendProfileManager:
    """
    Manages backend profiles and active profile selection.

    Provides CRUD operations for backend profiles and handles
    active profile management.
    """

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)
        self._profiles: Dict[str, BackendProfile] = {}
        self._active_profile_id: Optional[str] = None

        # Create default profile
        self._create_default_profile()

    def _create_default_profile(self) -> None:
        """Create the default backend profile"""
        default_profile = BackendProfile(
            name="Local Development",
            host="localhost",
            port=8000,
            use_ssl=False,
            description="Default local development server",
        )

        profile_id = "default"
        self._profiles[profile_id] = default_profile
        self._active_profile_id = profile_id

        self.logger.info(
            "Default backend profile created",
            config_event="default_profile_created",
            module=__name__,
            profile_id=profile_id,
            profile=str(default_profile),
        )

    def add_profile(self, profile_id: str, profile: BackendProfile) -> None:
        """
        Add a new backend profile.

        Args:
            profile_id: Unique identifier for the profile
            profile: BackendProfile instance

        Raises:
            ValueError: If profile_id already exists or is invalid
        """
        if not profile_id or not profile_id.strip():
            raise ValueError("Profile ID cannot be empty")

        if profile_id in self._profiles:
            raise ValueError(f"Profile with ID '{profile_id}' already exists")

        # Validate profile
        profile._validate()

        self._profiles[profile_id] = profile

        self.logger.info(
            "Backend profile added",
            config_event="profile_added",
            module=__name__,
            profile_id=profile_id,
            profile=str(profile),
        )

    def remove_profile(self, profile_id: str) -> None:
        """
        Remove a backend profile.

        Args:
            profile_id: Profile identifier to remove

        Raises:
            ValueError: If profile doesn't exist or is the active profile
        """
        if profile_id not in self._profiles:
            raise ValueError(f"Profile '{profile_id}' does not exist")

        if profile_id == self._active_profile_id:
            raise ValueError(
                "Cannot remove active profile. Switch to another profile first."
            )

        if profile_id == "default":
            raise ValueError("Cannot remove default profile")

        del self._profiles[profile_id]

        self.logger.info(
            "Backend profile removed",
            config_event="profile_removed",
            module=__name__,
            profile_id=profile_id,
        )

    def get_profile(self, profile_id: str) -> Optional[BackendProfile]:
        """Get a specific backend profile by ID"""
        return self._profiles.get(profile_id)

    def get_active_profile(self) -> Optional[BackendProfile]:
        """Get the currently active backend profile"""
        if self._active_profile_id:
            return self._profiles.get(self._active_profile_id)
        return None

    def get_active_profile_id(self) -> Optional[str]:
        """Get the currently active profile ID"""
        return self._active_profile_id

    def set_active_profile(self, profile_id: str) -> None:
        """
        Set the active backend profile.

        Args:
            profile_id: Profile identifier to activate

        Raises:
            ValueError: If profile doesn't exist
        """
        if profile_id not in self._profiles:
            raise ValueError(f"Profile '{profile_id}' does not exist")

        old_profile_id = self._active_profile_id
        self._active_profile_id = profile_id

        self.logger.info(
            "Active backend profile changed",
            config_event="active_profile_changed",
            module=__name__,
            old_profile_id=old_profile_id,
            new_profile_id=profile_id,
            profile=str(self._profiles[profile_id]),
        )

    def list_profiles(self) -> Dict[str, BackendProfile]:
        """Get all available backend profiles"""
        return self._profiles.copy()

    def list_profile_names(self) -> Dict[str, str]:
        """Get mapping of profile IDs to names"""
        return {pid: profile.name for pid, profile in self._profiles.items()}

    def update_profile(self, profile_id: str, profile: BackendProfile) -> None:
        """
        Update an existing backend profile.

        Args:
            profile_id: Profile identifier to update
            profile: Updated BackendProfile instance

        Raises:
            ValueError: If profile doesn't exist
        """
        if profile_id not in self._profiles:
            raise ValueError(f"Profile '{profile_id}' does not exist")

        # Validate updated profile
        profile._validate()

        self._profiles[profile_id] = profile

        self.logger.info(
            "Backend profile updated",
            config_event="profile_updated",
            module=__name__,
            profile_id=profile_id,
            profile=str(profile),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert all profiles to dictionary for JSON serialization"""
        return {
            "active_profile": self._active_profile_id,
            "profiles": {
                pid: profile.to_dict() for pid, profile in self._profiles.items()
            },
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load profiles from dictionary (JSON deserialization)"""
        self._profiles.clear()

        # Load profiles
        profiles_data = data.get("profiles", {})
        for profile_id, profile_data in profiles_data.items():
            try:
                profile = BackendProfile.from_dict(profile_data)
                self._profiles[profile_id] = profile
            except Exception as e:
                self.logger.warning(
                    "Failed to load backend profile",
                    config_event="profile_load_failed",
                    module=__name__,
                    profile_id=profile_id,
                    error=str(e),
                )

        # Set active profile
        active_profile_id = data.get("active_profile")
        if active_profile_id and active_profile_id in self._profiles:
            self._active_profile_id = active_profile_id
        else:
            # Fallback to first available profile or create default
            if self._profiles:
                self._active_profile_id = next(iter(self._profiles.keys()))
            else:
                self._create_default_profile()

        self.logger.info(
            "Backend profiles loaded from configuration",
            config_event="profiles_loaded",
            module=__name__,
            profile_count=len(self._profiles),
            active_profile_id=self._active_profile_id,
        )


# Export only necessary symbols per PROJECT_RULES.md
__all__ = [
    "ConnectionType",
    "BackendProfile",
    "BackendProfileManager",
]
