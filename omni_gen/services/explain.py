"""Explanation service for Chinese words, idioms, sayings."""

import hashlib

from omni_gen.cache import CacheManager
from omni_gen.config import get_settings
from omni_gen.models.base import BaseClient


class ExplainService:
    """Explanation service for Chinese words with caching support."""

    def __init__(self):
        """Initialize explain service."""
        settings = get_settings()
        # Use explain-specific config if available, otherwise fall back to OpenAI
        if settings.explain_api_key:
            self.base_url = settings.explain_base_url
            self.api_key = settings.explain_api_key
            self.model = settings.explain_model
        else:
            self.base_url = settings.openai_base_url
            self.api_key = settings.openai_api_key
            self.model = settings.openai_model

        self.client = BaseClient(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
        )
        self.prompt_template = settings.explain_prompt
        self.cache = CacheManager("explain")

    async def explain(self, text: str) -> tuple[str, str]:
        """Explain Chinese text (words, idioms, sayings).

        Args:
            text: Chinese text to explain

        Returns:
            Tuple of (filtered_text, full_text_with_think_content)
        """
        # Check cache
        content_hash = hashlib.md5(
            f"explain:{text}:{self.model}".encode()
        ).hexdigest()

        cached = self.cache.load(content_hash, "txt")
        if cached:
            full_text = cached.decode("utf-8")
            filtered_text = self._filter_think_content(full_text)
            return filtered_text.strip(), full_text.strip()

        # Call API
        prompt = self.prompt_template.format(source_text=text)

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.3,
            },
        )
        response.raise_for_status()
        data = response.json()

        full_text = data["choices"][0]["message"]["content"]

        # Save to cache
        self.cache.save(content_hash, "txt", full_text.encode("utf-8"))

        filtered_text = self._filter_think_content(full_text)
        return filtered_text.strip(), full_text.strip()

    def _filter_think_content(self, text: str) -> str:
        """Remove think content from text."""
        filtered = text
        # Remove <think>...</think> tags
        import re
        filtered = re.sub(r'<think>[\s\S]*?</think>', '', filtered)
        # Remove 【...】 tags
        filtered = re.sub(r'【[\s\S]*?】', '', filtered)
        return filtered.strip()

    async def close(self):
        """Close the service client."""
        await self.client.close()