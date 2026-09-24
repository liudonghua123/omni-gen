"""Translation service."""

import hashlib

from omni_gen.cache import CacheManager
from omni_gen.models.base import BaseClient
from omni_gen.runtime_config import get_runtime_config


class TranslateService:
    """Translation service using AI models with caching support."""

    def __init__(self):
        """Initialize translate service."""
        config = get_runtime_config()
        # Use translate-specific config if API key is set, otherwise fall back to OpenAI
        openai_base_url = config.get("OPENAI_BASE_URL", "")
        openai_api_key = config.get("OPENAI_API_KEY", "")
        openai_model = config.get("OPENAI_MODEL", "gpt-4o-mini")

        if config.get("TRANSLATE_API_KEY"):
            self.base_url = config.get("TRANSLATE_BASE_URL") or openai_base_url
            self.api_key = config.get("TRANSLATE_API_KEY")
            self.model = config.get("TRANSLATE_MODEL") or openai_model
        elif config.get("TRANSLATE_BASE_URL") and config.get("TRANSLATE_BASE_URL") != openai_base_url:
            # If base_url is explicitly set but no API key, use OpenAI key with custom base_url
            self.base_url = config.get("TRANSLATE_BASE_URL")
            self.api_key = openai_api_key
            self.model = openai_model
        else:
            self.base_url = openai_base_url
            self.api_key = openai_api_key
            self.model = openai_model

        self.client = BaseClient(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
        )
        self.default_target_lang = config.get("TRANSLATE_DEFAULT_TARGET_LANG", "en_US")
        self.prompt_template = config.get("TRANSLATE_PROMPT", "请将以下文本翻译成{target_lang}：\n{source_text}")
        self.cache = CacheManager("translate")

    async def translate(
        self,
        source_text: str,
        target_lang: str | None = None,
        prompt: str | None = None,
        refresh: bool = False,
    ) -> tuple[str, str]:
        """Translate text to target language.

        Args:
            source_text: Text to translate
            target_lang: Target language code (e.g., "en_US", "zh_CN")
            prompt: Custom prompt template (supports {source_text}, {target_lang})
                   If None, uses default from config
            refresh: If True, bypass cache and regenerate (default: False)

        Returns:
            Tuple of (translated_text, full_text_with_think_content)
        """
        target_lang = target_lang or self.default_target_lang
        prompt_template = prompt if prompt else self.prompt_template

        # Check cache (only if not refreshing)
        cache_key = f"translate:{source_text}:{target_lang}:{self.model}"
        if prompt:
            cache_key += f":{hash(prompt) % 100000}"
        content_hash = hashlib.md5(cache_key.encode()).hexdigest()

        if not refresh:
            cached = self.cache.load(content_hash, "txt")
            if cached:
                full_text = cached.decode("utf-8")
                translated_text = self._filter_think_content(full_text)
                return translated_text.strip(), full_text.strip()

        # Call API
        prompt_text = prompt_template.format(
            target_lang=target_lang,
            source_text=source_text,
        )

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt_text}],
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
