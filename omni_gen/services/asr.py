"""ASR (Automatic Speech Recognition) service."""

import hashlib
from pathlib import Path

from omni_gen.cache import CacheManager
from omni_gen.models.base import BaseClient
from omni_gen.runtime_config import get_runtime_config


class ASRService:
    """ASR (Speech-to-Text) service."""

    def __init__(self):
        """Initialize ASR service."""
        config = get_runtime_config()
        self.model = config.get("ASR_MODEL", "whisper-1")
        self.client = BaseClient(
            base_url=config.get("ASR_BASE_URL", "https://api.openai.com"),
            api_key=config.get("ASR_API_KEY", ""),
            model=self.model,
        )
        self.cache = CacheManager("audio")

    async def transcribe(
        self, audio_data: bytes, filename: str = "audio.wav", language: str = ""
    ) -> tuple[str, Path]:
        """Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes
            filename: Original filename for format detection
            language: Language code (e.g., "en", "zh") or empty for auto-detect

        Returns:
            Tuple of (transcribed_text, cache_path)
        """
        content_hash = hashlib.md5(f"asr:{audio_data[:1024]}:{self.model}".encode()).hexdigest()

        # Save audio to cache
        ext = Path(filename).suffix.lstrip(".") or "wav"
        cache_path = self.cache.save(content_hash, ext, audio_data)

        # Prepare multipart form data
        files = {"file": (filename, audio_data, f"audio/{ext}")}
        data = {"model": self.model}
        if language:
            data["language"] = language

        # Transcribe
        response = await self.client.client.post(
            f"{self.client.base_url}/audio/transcriptions",
            files=files,
            data=data,
        )
        response.raise_for_status()
        result = response.json()

        return result["text"], cache_path

    async def close(self):
        """Close the service client."""
        await self.client.close()
