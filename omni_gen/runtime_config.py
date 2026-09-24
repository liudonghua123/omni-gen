"""Runtime configuration manager with in-memory caching."""

import threading
from typing import Any, Optional

from omni_gen import db


class RuntimeConfig:
    """Runtime configuration manager with in-memory caching."""

    _instance: Optional["RuntimeConfig"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize runtime config."""
        self._config: dict[str, Any] = {}
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "RuntimeConfig":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load(self):
        """Load configuration from database into memory."""
        with self._lock:
            self._config = db.get_all_config()
            self._loaded = True

    def is_loaded(self) -> bool:
        """Check if config is loaded."""
        return self._loaded

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key."""
        if not self._loaded:
            self.load()

        if key in self._config:
            return self._config[key].get("value", default)
        return default

    def get_raw(self, key: str) -> dict | None:
        """Get raw config entry including metadata."""
        if not self._loaded:
            self.load()
        return self._config.get(key)

    def set(self, key: str, value: Any, description: str = None, category: str = None):
        """Set a config value in database and update memory cache."""
        # Update database
        db.set_config(key, value, description, category)

        # Update memory cache
        with self._lock:
            self._config[key] = {
                "value": value,
                "description": description or self._config.get(key, {}).get("description"),
                "category": category or self._config.get(key, {}).get("category"),
            }

    def get_all(self) -> dict[str, Any]:
        """Get all config values as a dictionary."""
        if not self._loaded:
            self.load()
        return {key: entry["value"] for key, entry in self._config.items()}

    def get_by_category(self, category: str) -> dict[str, Any]:
        """Get all config values in a category."""
        if not self._loaded:
            self.load()
        result = {}
        for key, entry in self._config.items():
            if entry.get("category") == category:
                result[key] = entry["value"]
        return result

    def get_categories(self) -> list[str]:
        """Get all config categories."""
        if not self._loaded:
            self.load()
        categories = set()
        for entry in self._config.values():
            if entry.get("category"):
                categories.add(entry["category"])
        return sorted(list(categories))

    def reload(self):
        """Reload configuration from database."""
        with self._lock:
            self._config = db.get_all_config()
            self._loaded = True


# Global instance
def get_runtime_config() -> RuntimeConfig:
    """Get the global runtime config instance."""
    return RuntimeConfig.get_instance()


def init_config():
    """Initialize database and load config into memory."""
    import hashlib as _hashlib

    # Initialize database
    db.init_database()

    # Initialize config from .env if database is empty
    existing = db.get_all_config()
    if not existing:
        db.init_config_from_env()
    else:
        # Check if ADMIN_PASSWORD needs to be re-initialized as hash
        stored = db.get_config("ADMIN_PASSWORD")
        if stored and len(stored) == 32:
            # It's a SHA256 hash (64 hex chars), not plain text
            pass
        else:
            # It's plain text, hash it
            from omni_gen.config import get_settings
            settings = get_settings()
            hashed = _hashlib.sha256(settings.admin_password.encode()).hexdigest()
            db.set_config("ADMIN_PASSWORD", hashed, "Admin password (hashed)", "Admin")
            # Reload to reflect change
            db.init_database()

    # Load into runtime
    config = get_runtime_config()
    config.load()

    # Set default admin password if not set
    if not db.get_config("ADMIN_PASSWORD"):
        db.set_admin_password("admin123")


# Import hashlib and hmac for password functions
import hashlib
import hmac