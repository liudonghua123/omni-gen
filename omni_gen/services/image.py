"""Image generation service."""

import hashlib
from pathlib import Path

from omni_gen.cache import CacheManager
from omni_gen.config import get_settings
from omni_gen.models.base import BaseClient


class ImageService:
    """Image generation service with caching support."""

    def __init__(self):
        """Initialize image service."""
        settings = get_settings()
        self.model = settings.image_model
        self.client = BaseClient(
            base_url=settings.image_base_url,
            api_key=settings.image_api_key,
            model=self.model,
        )
        self.cache = CacheManager("images")

    async def generate(
        self, prompt: str, size: str = "1024x1024", quality: str = "standard"
    ) -> tuple[bytes, Path]:
        """Generate image from text prompt.

        Args:
            prompt: Text description of the image
            size: Image size (e.g., "1024x1024")
            quality: Image quality ("standard" or "hd")

        Returns:
            Tuple of (image_bytes, file_path)
        """
        content_hash = hashlib.md5(
            f"image:{prompt}:{size}:{quality}:{self.model}".encode()
        ).hexdigest()

        # Check cache
        cached = self.cache.load(content_hash, "png")
        if cached:
            return cached, self.cache.get_path(content_hash, "png")

        # Generate image
        response = await self.client.post(
            "/images/generations",
            json={
                "model": self.model,
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "response_format": "b64_json",
            },
        )
        response.raise_for_status()
        data = response.json()

        import base64

        image_bytes = base64.b64decode(data["data"][0]["b64_json"])

        # Save to cache
        path = self.cache.save(content_hash, "png", image_bytes)
        return image_bytes, path

    async def close(self):
        """Close the service client."""
        await self.client.close()
