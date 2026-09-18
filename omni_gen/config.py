"""Configuration management using dotenv."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    app_base_url: str = "http://localhost:8000"

    # Paths
    cache_dir: Path = Path("./cache")

    # OpenAI (Generic AI)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # TTS
    tts_base_url: str = "https://new-api.app.ynu.edu.cn/v1"
    tts_api_key: str = ""
    tts_model: str = "bosonai/higgs-audio-v3-tts-4b"
    tts_default_format: str = "wav"

    # Image Generation
    image_base_url: str = "https://new-api.app.ynu.edu.cn/v1"
    image_api_key: str = ""
    image_model: str = "dall-e-3"

    # ASR
    asr_base_url: str = "https://new-api.app.ynu.edu.cn/v1"
    asr_api_key: str = ""
    asr_model: str = "whisper-1"

    # Translate
    translate_base_url: str = "https://api.openai.com/v1"
    translate_api_key: str = ""
    translate_model: str = "gpt-4o-mini"
    translate_default_target_lang: str = "en_US"
    translate_prompt: str = "Translate the following text into {target_lang}. Note that you should only output the translated result without any additional explanation:\n\n{source_text}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
