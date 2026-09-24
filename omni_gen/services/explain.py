"""Explanation service for Chinese words, idioms, sayings."""

import hashlib

from omni_gen.cache import CacheManager
from omni_gen.models.base import BaseClient
from omni_gen.runtime_config import get_runtime_config


class ExplainService:
    """Explanation service for Chinese words with caching support."""

    def __init__(self):
        """Initialize explain service."""
        config = get_runtime_config()
        # Use explain-specific config if API key is set, otherwise fall back to OpenAI
        openai_base_url = config.get("OPENAI_BASE_URL", "")
        openai_api_key = config.get("OPENAI_API_KEY", "")
        openai_model = config.get("OPENAI_MODEL", "gpt-4o-mini")

        if config.get("EXPLAIN_API_KEY"):
            self.base_url = config.get("EXPLAIN_BASE_URL") or openai_base_url
            self.api_key = config.get("EXPLAIN_API_KEY")
            self.model = config.get("EXPLAIN_MODEL") or openai_model
        elif config.get("EXPLAIN_BASE_URL") and config.get("EXPLAIN_BASE_URL") != openai_base_url:
            # If base_url is explicitly set but no API key, use OpenAI key with custom base_url
            self.base_url = config.get("EXPLAIN_BASE_URL")
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
        self.prompt_template = config.get("EXPLAIN_PROMPT", "请详细解释以下中文词汇，包括词义、用法、例句等：\n{content}")
        self.cache = CacheManager("explain")

    async def explain(self, text: str, prompt: str | None = None, refresh: bool = False) -> tuple[str, str]:
        """Explain Chinese text (words, idioms, sayings).

        Args:
            text: Chinese text to explain
            prompt: Custom prompt template (supports {content})
                   If None, uses default from config
            refresh: If True, bypass cache and regenerate (default: False)

        Returns:
            Tuple of (filtered_text, full_text_with_think_content)
        """
        prompt_template = prompt if prompt else self.prompt_template

        # Check cache (only if not refreshing)
        cache_key = f"explain:{text}:{self.model}"
        if prompt:
            cache_key += f":{hash(prompt) % 100000}"
        content_hash = hashlib.md5(cache_key.encode()).hexdigest()

        if not refresh:
            cached = self.cache.load(content_hash, "txt")
            if cached:
                full_text = cached.decode("utf-8")
                filtered_text = self._filter_think_content(full_text)
                return filtered_text.strip(), full_text.strip()

        # Call API
        prompt_text = prompt_template.replace("{content}", text)

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt_text}],
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
