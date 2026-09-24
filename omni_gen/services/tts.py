"""TTS (Text-to-Speech) service."""

import hashlib
import subprocess
from pathlib import Path
from typing import Optional

from omni_gen.cache import CacheManager
from omni_gen.models.base import BaseClient
from omni_gen.runtime_config import get_runtime_config


class TTSService:
    """Text-to-Speech service with caching support."""

    def __init__(self):
        """Initialize TTS service."""
        config = get_runtime_config()
        self.model = config.get("TTS_MODEL", "tts-1")
        self.client = BaseClient(
            base_url=config.get("TTS_BASE_URL", "https://api.openai.com"),
            api_key=config.get("TTS_API_KEY", ""),
            model=self.model,
        )
        self.default_format = config.get("TTS_DEFAULT_FORMAT", "mp3")
        self.cache = CacheManager("audio")

    async def synthesize(
        self, text: str, format: Optional[str] = None
    ) -> tuple[bytes, Path]:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            format: Output format (wav/mp3), defaults to config setting

        Returns:
            Tuple of (audio_bytes, file_path)
        """
        fmt = format or self.default_format
        content_hash = hashlib.md5(f"tts:{text}:{self.model}".encode()).hexdigest()

        # Check cache
        cached = self.cache.load(content_hash, fmt)
        if cached:
            return cached, self.cache.get_path(content_hash, fmt)

        # Generate audio (API returns wav)
        response = await self.client.post(
            "/audio/speech",
            json={
                "model": self.model,
                "input": text,
            },
        )
        response.raise_for_status()
        audio_bytes = response.content

        # Save original wav to cache
        wav_path = self.cache.save(content_hash, "wav", audio_bytes)

        # Convert if needed
        if fmt == "wav":
            return audio_bytes, wav_path
        else:
            mp3_path = self.cache.save(content_hash, "mp3", await self._convert(wav_path, "mp3"))
            if fmt == "mp3":
                mp3_bytes = self.cache.load(content_hash, "mp3")
                assert mp3_bytes is not None
                return mp3_bytes, mp3_path

        return audio_bytes, wav_path

    async def _convert(self, input_path: Path, output_format: str) -> bytes:
        """Convert audio file to different format using ffmpeg."""

        output_path = input_path.with_suffix(f".{output_format}")

        cmd = ["ffmpeg", "-y", "-i", str(input_path), str(output_path)]
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg conversion failed: {result.stderr.decode()}")

        return output_path.read_bytes()

    async def close(self):
        """Close the service client."""
        await self.client.close()
