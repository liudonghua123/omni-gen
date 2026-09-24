"""Database management for configuration storage."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from omni_gen.config import get_settings


DB_PATH = Path(__file__).parent.parent / "config.db"


def get_db_path() -> Path:
    """Get the database path."""
    return DB_PATH


@contextmanager
def get_db_connection():
    """Get a database connection context manager."""
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize the database with config table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Create config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                category TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Create admin_users table for password management
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_all_config() -> dict[str, dict[str, Any]]:
    """Get all configuration from database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value, description, category FROM config")
        rows = cursor.fetchall()

        config = {}
        for row in rows:
            key = row["key"]
            value = row["value"]
            # Try to parse JSON value
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value
            config[key] = {
                "value": parsed_value,
                "description": row["description"],
                "category": row["category"],
            }
        return config


def get_config(key: str) -> str | None:
    """Get a single config value by key."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row["value"])
            except json.JSONDecodeError:
                return row["value"]
        return None


def set_config(key: str, value: Any, description: str = None, category: str = None):
    """Set a config value in the database."""
    # Convert value to JSON string if needed
    if isinstance(value, (dict, list, bool)):
        value_str = json.dumps(value)
    else:
        value_str = str(value)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO config (key, value, description, category)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                description = COALESCE(excluded.description, description),
                category = COALESCE(excluded.category, category),
                updated_at = CURRENT_TIMESTAMP
        """, (key, value_str, description, category))
        conn.commit()


def delete_config(key: str):
    """Delete a config value from the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config WHERE key = ?", (key,))
        conn.commit()


def get_config_categories() -> list[str]:
    """Get all unique config categories."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM config WHERE category IS NOT NULL")
        return [row["category"] for row in cursor.fetchall()]


def init_config_from_env():
    """Initialize database with values from .env file."""
    import hashlib

    from omni_gen.config import get_settings
    settings = get_settings()

    # Define config categories and descriptions
    config_definitions = {
        # Server
        "HOST": {"value": settings.host, "category": "Server", "description": "Server host"},
        "PORT": {"value": settings.port, "category": "Server", "description": "Server port"},
        "DEBUG": {"value": settings.debug, "category": "Server", "description": "Debug mode"},
        "APP_BASE_URL": {"value": str(settings.app_base_url), "category": "Server", "description": "App base URL"},

        # Paths
        "CACHE_DIR": {"value": str(settings.cache_dir), "category": "Paths", "description": "Cache directory"},

        # OpenAI
        "OPENAI_BASE_URL": {"value": settings.openai_base_url, "category": "OpenAI", "description": "OpenAI base URL"},
        "OPENAI_API_KEY": {"value": settings.openai_api_key, "category": "OpenAI", "description": "OpenAI API key"},
        "OPENAI_MODEL": {"value": settings.openai_model, "category": "OpenAI", "description": "OpenAI model"},

        # TTS
        "TTS_BASE_URL": {"value": settings.tts_base_url, "category": "TTS", "description": "TTS base URL"},
        "TTS_API_KEY": {"value": settings.tts_api_key, "category": "TTS", "description": "TTS API key"},
        "TTS_MODEL": {"value": settings.tts_model, "category": "TTS", "description": "TTS model"},
        "TTS_DEFAULT_FORMAT": {"value": settings.tts_default_format, "category": "TTS", "description": "Default audio format"},

        # Image
        "IMAGE_BASE_URL": {"value": settings.image_base_url, "category": "Image", "description": "Image API base URL"},
        "IMAGE_API_KEY": {"value": settings.image_api_key, "category": "Image", "description": "Image API key"},
        "IMAGE_MODEL": {"value": settings.image_model, "category": "Image", "description": "Image model"},

        # ASR
        "ASR_BASE_URL": {"value": settings.asr_base_url, "category": "ASR", "description": "ASR base URL"},
        "ASR_API_KEY": {"value": settings.asr_api_key, "category": "ASR", "description": "ASR API key"},
        "ASR_MODEL": {"value": settings.asr_model, "category": "ASR", "description": "ASR model"},

        # Translate
        "TRANSLATE_BASE_URL": {"value": settings.translate_base_url, "category": "Translate", "description": "Translate base URL"},
        "TRANSLATE_API_KEY": {"value": settings.translate_api_key, "category": "Translate", "description": "Translate API key"},
        "TRANSLATE_MODEL": {"value": settings.translate_model, "category": "Translate", "description": "Translate model"},
        "TRANSLATE_DEFAULT_TARGET_LANG": {"value": settings.translate_default_target_lang, "category": "Translate", "description": "Default target language"},
        "TRANSLATE_PROMPT": {"value": settings.translate_prompt, "category": "Translate", "description": "Translate prompt template"},

        # Explain
        "EXPLAIN_BASE_URL": {"value": settings.explain_base_url, "category": "Explain", "description": "Explain base URL"},
        "EXPLAIN_API_KEY": {"value": settings.explain_api_key, "category": "Explain", "description": "Explain API key"},
        "EXPLAIN_MODEL": {"value": settings.explain_model, "category": "Explain", "description": "Explain model"},
        "EXPLAIN_PROMPT": {"value": settings.explain_prompt, "category": "Explain", "description": "Explain prompt template"},

        # Practise
        "PRACTISE_BASE_URL": {"value": settings.practise_base_url, "category": "Practise", "description": "Practise base URL"},
        "PRACTISE_API_KEY": {"value": settings.practise_api_key, "category": "Practise", "description": "Practise API key"},
        "PRACTISE_MODEL": {"value": settings.practise_model, "category": "Practise", "description": "Practise model"},
        "PRACTISE_PROMPT": {"value": settings.practise_prompt, "category": "Practise", "description": "Practise prompt template"},

        # Admin
        "ADMIN_PASSWORD": {"value": hashlib.sha256(settings.admin_password.encode()).hexdigest(), "category": "Admin", "description": "Admin password (hashed)"},
    }

    # Insert all config values
    for key, data in config_definitions.items():
        set_config(key, data["value"], data["description"], data["category"])


def check_admin_password(password: str) -> bool:
    """Check if the provided password matches the admin password."""
    import hashlib
    import hmac

    stored_hash = get_config("ADMIN_PASSWORD")
    if not stored_hash:
        return False

    # Hash the provided password
    provided_hash = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(stored_hash, provided_hash)


def set_admin_password(password: str):
    """Set the admin password (stores hashed version)."""
    import hashlib
    hashed = hashlib.sha256(password.encode()).hexdigest()
    set_config("ADMIN_PASSWORD", hashed, "Admin password (hashed)", "Admin")