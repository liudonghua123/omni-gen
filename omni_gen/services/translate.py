"""Translation service."""

import hashlib

from omni_gen.cache import CacheManager
from omni_gen.config import get_settings
from omni_gen.models.base import BaseClient


class TranslateService:
    """Translation service using AI models with caching support."""

    def __init__(self):
        """Initialize translate service."""
        settings = get_settings()
        # Use translate-specific config if available, otherwise fall back to OpenAI
        if settings.translate_api_key:
            self.base_url = settings.translate_base_url
            self.api_key = settings.translate_api_key
            self.model = settings.translate_model
        else:
            self.base_url = settings.openai_base_url
            self.api_key = settings.openai_api_key
            self.model = settings.openai_model

        self.client = BaseClient(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
        )
        self.default_target_lang = settings.translate_default_target_lang
        self.prompt_template = settings.translate_prompt
        self.cache = CacheManager("translate")

    async def translate(
        self, source_text: str, target_lang: str | None = None
    ) -> tuple[str, str]:
        """Translate text to target language.

        Args:
            source_text: Text to translate
            target_lang: Target language code (e.g., "en_US", "zh_CN")

        Returns:
            Tuple of (translated_text, full_text_with_think_content)
        """
        target_lang = target_lang or self.default_target_lang

        # Check cache
        content_hash = hashlib.md5(
            f"translate:{source_text}:{target_lang}:{self.model}".encode()
        ).hexdigest()

        cached = self.cache.load(content_hash, "txt")
        if cached:
            full_text = cached.decode("utf-8")
            translated_text = self._filter_think_content(full_text)
            return translated_text.strip(), full_text.strip()

        # Call API
        prompt = self.prompt_template.format(
            target_lang=target_lang,
            source_text=source_text,
        )

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

        translated_text = self._filter_think_content(full_text)
        return translated_text.strip(), full_text.strip()

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