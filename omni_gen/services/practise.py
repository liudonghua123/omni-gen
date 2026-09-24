"""Practise question generation service."""

import hashlib
import json
import logging
import re
from typing import Optional

from omni_gen.cache import CacheManager
from omni_gen.models.base import BaseClient
from omni_gen.runtime_config import get_runtime_config

logger = logging.getLogger(__name__)


class PractiseService:
    """Practise question generation service with caching support."""

    def __init__(self):
        """Initialize practise service."""
        config = get_runtime_config()
        # Use practise-specific config if API key is set, otherwise fall back to OpenAI
        openai_base_url = config.get("OPENAI_BASE_URL", "")
        openai_api_key = config.get("OPENAI_API_KEY", "")
        openai_model = config.get("OPENAI_MODEL", "gpt-4o-mini")

        if config.get("PRACTISE_API_KEY"):
            self.base_url = config.get("PRACTISE_BASE_URL") or openai_base_url
            self.api_key = config.get("PRACTISE_API_KEY")
            self.model = config.get("PRACTISE_MODEL") or openai_model
        elif config.get("PRACTISE_BASE_URL") and config.get("PRACTISE_BASE_URL") != openai_base_url:
            # If base_url is explicitly set but no API key, use OpenAI key with custom base_url
            self.base_url = config.get("PRACTISE_BASE_URL")
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
        self.prompt_template = config.get("PRACTISE_PROMPT",
            "你是一个出题专家，请根据用户给定的主题生成{count}道{types}题目。\n\n"
            "要求：\n"
            "1. 题目内容要准确、严谨，避免歧义\n"
            "2. 各题目之间不要重复\n"
            "3. 只返回JSON数组，不要包含其他内容\n"
            "4. 使用标准的JSON格式\n\n"
            "请直接返回JSON格式的题目数组，格式如下：\n"
            '```json\n'
            '[\n'
            '  {\n'
            '    "title": "题干内容",\n'
            '    "type": "single_choice|multiple_choice|true_false",\n'
            '    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],\n'
            '    "answer": ["A"],\n'
            '    "analysis": "解析内容"\n'
            '  }\n'
            ']\n'
            "```\n\n"
            "主题：{topic}\n"
            "题目数量：{count}\n"
            "题目类型：{types}")
        self.cache = CacheManager("practise")

    async def generate_practise(
        self,
        topic: str,
        count: int = 5,
        types: Optional[list[str]] = None,
        prompt: str | None = None,
        refresh: bool = False,
    ) -> tuple[list[dict], str]:
        """Generate practise questions.

        Args:
            topic: The topic/theme for generating questions
            count: Number of questions to generate
            types: List of question types ("single_choice", "multiple_choice", "true_false")
                  If None, all types are included
            prompt: Custom prompt template (supports {topic}, {count}, {types}, {types_en})
                   If None, uses default from config
            refresh: If True, bypass cache and regenerate (default: False)

        Returns:
            Tuple of (filtered_questions, full_response)
        """
        if types is None:
            types = ["single_choice", "multiple_choice", "true_false"]

        prompt_template = prompt if prompt else self.prompt_template

        # Check cache (only if not refreshing)
        cache_key = f"practise:{topic}:{count}:{','.join(sorted(types))}:{self.model}"
        if prompt:
            cache_key += f":{hash(prompt) % 100000}"
        content_hash = hashlib.md5(cache_key.encode()).hexdigest()

        if not refresh:
            cached = self.cache.load(content_hash, "json")
            if cached:
                logger.info("[Practise] Cache HIT, loading from cache")
                data = json.loads(cached.decode("utf-8"))
                return data["questions"], data["full_response"]

        logger.info("[Practise] Cache MISS, calling API...")

        # Call API
        # Replace all common placeholders so custom prompts work regardless of variable name
        prompt_text = (prompt_template
            .replace("{topic}", topic)
            .replace("{count}", str(count))
            .replace("{types}", "、".join([self._type_to_chinese(t) for t in types]))
            .replace("{types_en}", ",".join(types)))

        try:
            logger.info(f"[Practise] Sending request to {self.base_url}/chat/completions")
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt_text}],
                },
            )

            data = response.json()
            logger.info(f"[Practise] API response keys: {list(data.keys())}")

            if "choices" not in data:
                logger.error(f"[Practise] No 'choices' in response! Full response: {data}")
                raise ValueError("Unexpected API response: no 'choices' key")

            if not data["choices"]:
                logger.error(f"[Practise] Empty choices! Full response: {data}")
                raise ValueError("Unexpected API response: empty choices")

            message = data["choices"][0].get("message", {})
            logger.info(f"[Practise] Message keys: {list(message.keys())}")

            if "content" not in message:
                logger.error(f"[Practise] No 'content' in message! Full message: {message}")
                raise ValueError("Unexpected API response: no 'content' in message")

            full_response = message["content"]
            logger.info(f"[Practise] Full response (length={len(full_response)}):\n{full_response[:1000]}")

        except Exception as e:
            logger.error(f"[Practise] Exception during API call: {type(e).__name__}: {e}")
            raise

        logger.info("[Practise] Parsing questions...")
        questions = self._parse_questions(full_response)
        logger.info(f"[Practise] Parsed {len(questions)} questions")

        # Save to cache
        cache_data = {
            "questions": questions,
            "full_response": full_response,
        }
        self.cache.save(content_hash, "json", json.dumps(cache_data, ensure_ascii=False).encode("utf-8"))
        logger.info("[Practise] Saved to cache")

        return questions, full_response

    def _type_to_chinese(self, qtype: str) -> str:
        """Convert question type to Chinese."""
        mapping = {
            "single_choice": "单选题",
            "multiple_choice": "多选题",
            "true_false": "判断题",
        }
        return mapping.get(qtype, qtype)

    def _parse_questions(self, text: str) -> list[dict]:
        """Parse questions from LLM response.

        Expected format:
        ```json
        [
          {
            "title": "题干内容",
            "type": "single_choice|multiple_choice|true_false",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": ["A"],
            "analysis": "解析内容"
          }
        ]
        ```
        """
        logger.info(f"[Practise] Raw LLM response (length={len(text)}):\n{text[:2000]}...")

        # Filter out think content first
        filtered_text = self._filter_think_content(text)
        logger.info(f"[Practise] After filtering (length={len(filtered_text)}):\n{filtered_text[:2000]}...")
        text_to_parse = filtered_text if filtered_text.strip() else text

        # Try to extract JSON from markdown code blocks first
        json_match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text_to_parse)
        if json_match:
            logger.info(f"[Practise] Found JSON in code block: {json_match.group(1)[:500]}...")
            try:
                questions = json.loads(json_match.group(1))
                return self._validate_and_normalize(questions)
            except json.JSONDecodeError as e:
                logger.warning(f"[Practise] Failed to parse code block JSON: {e}")

        # Try to find JSON array directly
        json_match = re.search(r"\[\s*\{[\s\S]*?\}\s*\]", text_to_parse)
        if json_match:
            logger.info(f"[Practise] Found JSON array: {json_match.group(0)[:500]}...")
            try:
                questions = json.loads(json_match.group(0))
                return self._validate_and_normalize(questions)
            except json.JSONDecodeError as e:
                logger.warning(f"[Practise] Failed to parse JSON array: {e}")

        # Fallback: try to parse the filtered text
        try:
            logger.info("[Practise] Trying to parse full text as JSON")
            questions = json.loads(text_to_parse)
            return self._validate_and_normalize(questions)
        except json.JSONDecodeError as e:
            logger.warning(f"[Practise] Failed to parse full text as JSON: {e}")
            # If all parsing fails, wrap the text as one question
            return [{
                "title": text_to_parse.strip() or text.strip(),
                "type": "single_choice",
                "options": [],
                "answer": [],
                "analysis": "解析失败，请检查返回格式",
            }]

    def _filter_think_content(self, text: str) -> str:
        """Remove think content from text."""
        filtered = text
        # Remove <think>...</think> tags
        filtered = re.sub(r'<think>[\s\S]*?</think>', '', filtered)
        # Remove 【...】 tags
        filtered = re.sub(r'【[\s\S]*?】', '', filtered)
        # Remove [THINK]...[/THINK] tags
        filtered = re.sub(r'\[THINK\][\s\S]*?\[/THINK\]', '', filtered, flags=re.IGNORECASE)
        # Remove \<think\>...\</think\> tags
        filtered = re.sub(r'<think>[\s\S]*?</think>', '', filtered, flags=re.IGNORECASE)
        # Remove XML-style think tags
        filtered = re.sub(r'<thinking>[\s\S]*?</thinking>', '', filtered, flags=re.IGNORECASE)
        logger.info(f"[Practise] Filtered think content, before: {len(text)} chars, after: {len(filtered)} chars")
        return filtered.strip()

    def _validate_and_normalize(self, questions: list) -> list[dict]:
        """Validate and normalize question format."""
        normalized = []
        for q in questions:
            if not isinstance(q, dict):
                continue

            # Ensure required fields
            question = {
                "title": str(q.get("title", "")),
                "type": self._normalize_type(q.get("type", "single_choice")),
                "options": q.get("options", []),
                "answer": q.get("answer", []),
                "analysis": str(q.get("analysis", "")),
            }

            # Validate type-specific requirements
            if question["type"] == "true_false":
                question["options"] = []  # No options for true/false
            elif not question["options"]:
                question["options"] = ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"]

            normalized.append(question)

        return normalized

    def _normalize_type(self, qtype: str) -> str:
        """Normalize question type to standard format."""
        qtype_lower = qtype.lower().replace("-", "_").replace(" ", "_")

        if "single" in qtype_lower or "单选" in qtype:
            return "single_choice"
        elif "multiple" in qtype_lower or "multi" in qtype_lower or "多选" in qtype:
            return "multiple_choice"
        elif "true" in qtype_lower or "false" in qtype_lower or "判断" in qtype:
            return "true_false"

        return "single_choice"

    async def close(self):
        """Close the service client."""
        await self.client.close()
