"""Cache manager for generated content."""

import hashlib
from pathlib import Path
from typing import Optional

from omni_gen.config import get_settings


def _ensure_cache_dir() -> Path:
    """Ensure cache directory exists."""
    settings = get_settings()
    cache_dir = settings.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _compute_hash(content: str) -> str:
    """Compute MD5 hash for cache key."""
    return hashlib.md5(content.encode()).hexdigest()


class CacheManager:
    """Manages file-based caching for generated content."""

    def __init__(self, subdir: str):
        """Initialize cache manager for a specific content type.

        Args:
            subdir: Subdirectory under cache root (e.g., 'audio', 'images')
        """
        self.subdir = subdir

    @property
    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        base = _ensure_cache_dir()
        path = base / self.subdir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_path(self, content_hash: str, extension: str) -> Path:
        """Get cache file path for given content and format."""
        return self.cache_dir / f"{content_hash}.{extension}"

    def exists(self, content_hash: str, extension: str) -> bool:
        """Check if cached content exists."""
        return self.get_path(content_hash, extension).exists()

    def save(self, content_hash: str, extension: str, data: bytes) -> Path:
        """Save content to cache and return path."""
        path = self.get_path(content_hash, extension)
        path.write_bytes(data)
        return path

    def load(self, content_hash: str, extension: str) -> Optional[bytes]:
        """Load content from cache if exists."""
        path = self.get_path(content_hash, extension)
        if path.exists():
            return path.read_bytes()
        return None
