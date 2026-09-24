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
    translate_prompt: str = "Translate the following text into {target_lang}. Note that you should only output the translated result without any additional explanation:\n\n{content}"

    # Explain (Chinese words, idioms, sayings)
    explain_base_url: str = "https://api.openai.com/v1"
    explain_api_key: str = ""
    explain_model: str = "gpt-4o-mini"
    explain_prompt: str = "请解释以下中文词语、成语或歇后语，包括其中文含义、英文翻译、以及在句子中的用法示例。注意只输出解释内容，不要有其他说明：\n\n{content}"

    # Practise (Question generation)
    practise_base_url: str = "https://api.openai.com/v1"
    practise_api_key: str = ""
    practise_model: str = "gpt-4o-mini"
    practise_prompt: str = """你是一个专业的习题生成专家。请根据以下主题生成习题。

主题：{topic}
题目数量：{count}
题目类型：{types}

请严格按照以下JSON格式返回，不要包含任何其他内容：
```json
[
  {{
    "title": "题干内容（这里是你的题目描述）",
    "type": "single_choice|multiple_choice|true_false",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "answer": ["A"] 或 ["A","B"] 或 ["true"] 等正确答案列表,
    "analysis": "题目解析，说明为什么选择这个答案"
  }}
]
```

要求：
1. 题目要有意义，能够测试学生对知识点的理解
2. 选项要合理，避免歧义
3. 答案要准确
4. 解析要清晰，帮助学生理解知识点
5. 单选题答案为单个选项如["A"]，多选题可以有多个选项如["A","C"]
6. 判断题 type 为 "true_false"，answer 为 ["true"] 或 ["false"]，不需要 options

请生成 {count} 道 {types} 题目："""

    # Admin
    admin_password: str = "admin123"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
