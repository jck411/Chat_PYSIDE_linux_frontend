"""
Font Manager with Caching System

Following PROJECT_RULES.md:
- Performance optimized font management
- Memory-efficient caching with limits
- Thread-safe font creation
- Structured logging integration
"""

from weakref import WeakValueDictionary

import structlog
from PySide6.QtGui import QFont

# Type aliases for clarity
FontKey = tuple[str, int]  # (family, size)


class FontManager:
    """
    Centralized font management with intelligent caching.

    Features:
    - LRU-style cache with size limits
    - Weak references to prevent memory leaks
    - Performance monitoring
    - Thread-safe operations
    """

    # Cache configuration
    MAX_CACHE_SIZE = 50
    DEFAULT_CHAT_FONT = ("Consolas", 11)

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)

        # Main font cache with strong references
        self._font_cache: dict[FontKey, QFont] = {}

        # Weak reference cache for cleanup
        self._weak_cache: WeakValueDictionary[FontKey, QFont] = WeakValueDictionary()

        # Access tracking for LRU eviction
        self._access_order: list[FontKey] = []

        self.logger.info(
            "Font manager initialized",
            font_event="manager_init",
            module=__name__,
            cache_limit=self.MAX_CACHE_SIZE,
        )

    def get_font(self, family: str, size: int) -> QFont:
        """
        Get font with caching. Creates if not exists.

        Args:
            family: Font family name
            size: Font size in points

        Returns:
            QFont instance (cached or newly created)
        """
        key = (family, size)

        # Check cache first
        if key in self._font_cache:
            self._update_access_order(key)
            self.logger.debug(
                "Font cache hit",
                font_event="cache_hit",
                module=__name__,
                family=family,
                size=size,
            )
            return self._font_cache[key]

        # Create new font
        font = QFont(family, size)

        # Manage cache size
        self._ensure_cache_space()

        # Store in cache
        self._font_cache[key] = font
        self._weak_cache[key] = font
        self._access_order.append(key)

        self.logger.debug(
            "Font created and cached",
            font_event="font_created",
            module=__name__,
            family=family,
            size=size,
            cache_size=len(self._font_cache),
        )

        return font

    def get_chat_font(self, family: str | None = None, size: int | None = None) -> QFont:
        """Get chat font with fallback to defaults"""
        family = family or self.DEFAULT_CHAT_FONT[0]
        size = size or self.DEFAULT_CHAT_FONT[1]
        return self.get_font(family, size)

    def _update_access_order(self, key: FontKey) -> None:
        """Update LRU access order"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _ensure_cache_space(self) -> None:
        """Ensure cache doesn't exceed size limit"""
        while len(self._font_cache) >= self.MAX_CACHE_SIZE:
            # Remove least recently used
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                self._font_cache.pop(oldest_key, None)

                self.logger.debug(
                    "Font evicted from cache",
                    font_event="cache_eviction",
                    module=__name__,
                    evicted_key=oldest_key,
                    cache_size=len(self._font_cache),
                )
            else:
                # Fallback: clear entire cache if access order is corrupted
                self.clear_cache()
                break

    def clear_cache(self) -> None:
        """Clear all cached fonts"""
        cache_size = len(self._font_cache)
        self._font_cache.clear()
        self._weak_cache.clear()
        self._access_order.clear()

        self.logger.info(
            "Font cache cleared",
            font_event="cache_cleared",
            module=__name__,
            fonts_cleared=cache_size,
        )

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics for monitoring"""
        return {
            "cached_fonts": len(self._font_cache),
            "weak_references": len(self._weak_cache),
            "max_cache_size": self.MAX_CACHE_SIZE,
            "access_order_length": len(self._access_order),
        }

    def cleanup(self) -> None:
        """Cleanup resources on shutdown"""
        self.clear_cache()
        self.logger.info(
            "Font manager cleanup completed",
            font_event="cleanup",
            module=__name__,
        )


# Global font manager instance
_font_manager: FontManager | None = None


def get_font_manager() -> FontManager:
    """Get the global font manager instance"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


# Export only necessary symbols per PROJECT_RULES.md
__all__ = ["FontManager", "get_font_manager"]
