"""MCP tools for omni-gen services."""

from fastmcp import FastMCP

from omni_gen.config import get_settings
from omni_gen.services import (
    ASRService,
    ExplainService,
    ImageService,
    PractiseService,
    TranslateService,
    TTSService,
)

# Create MCP server instance
mcp = FastMCP("omni-gen AI Tools")


def get_base_url() -> str:
    """Get the base URL from settings."""
    settings = get_settings()
    return settings.app_base_url.replace("\\", "/")


# TTS Tools
@mcp.tool
async def text_to_speech(
    text: str,
    format: str = "wav"
) -> dict:
    """Convert text to speech audio.

    Args:
        text: Text to convert to speech
        format: Audio format (wav or mp3)

    Returns:
        Dictionary with audio file path and metadata
    """
    service = TTSService()
    try:
        audio_bytes, path = await service.synthesize(text, format)
        base_url = get_base_url()
        relative_path = path.relative_to(get_settings().cache_dir).as_posix()
        return {
            "success": True,
            "file_path": f"{base_url}/cache/{relative_path}",
            "text": text,
            "format": format,
            "size_bytes": len(audio_bytes),
        }
    finally:
        await service.close()


# Image Generation Tools
@mcp.tool
async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard"
) -> dict:
    """Generate an image from a text description.

    Args:
        prompt: Text description of the image to generate
        size: Image size (e.g., "1024x1024", "1792x1024")
        quality: Image quality ("standard" or "hd")

    Returns:
        Dictionary with image file path and metadata
    """
    service = ImageService()
    try:
        image_bytes, path = await service.generate(prompt, size, quality)
        base_url = get_base_url()
        relative_path = path.relative_to(get_settings().cache_dir).as_posix()
        return {
            "success": True,
            "file_path": f"{base_url}/cache/{relative_path}",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "width": int(size.split("x")[0]),
            "height": int(size.split("x")[1]),
        }
    finally:
        await service.close()


# ASR Tools
@mcp.tool
async def speech_to_text(
    audio_base64: str,
    filename: str = "audio.wav",
    language: str = ""
) -> dict:
    """Transcribe speech audio to text.

    Args:
        audio_base64: Base64-encoded audio data
        filename: Original filename for format detection
        language: Language code (e.g., "en", "zh") or empty for auto-detect

    Returns:
        Dictionary with transcribed text and metadata
    """
    import base64

    service = ASRService()
    try:
        audio_bytes = base64.b64decode(audio_base64)
        text, path = await service.transcribe(audio_bytes, filename, language)
        base_url = get_base_url()
        relative_path = path.relative_to(get_settings().cache_dir).as_posix()
        return {
            "success": True,
            "text": text,
            "file_path": f"{base_url}/cache/{relative_path}",
            "language_detected": language or "auto",
        }
    finally:
        await service.close()


# Translate Tools
@mcp.tool
async def translate_text(
    content: str,
    target_lang: str = "en_US",
    prompt: str | None = None,
    refresh: bool = False,
) -> dict:
    """Translate text to target language.

    Args:
        content: Text to translate
        target_lang: Target language code (e.g., "en_US", "zh_CN")
        prompt: Custom prompt template (optional)
        refresh: If True, bypass cache and regenerate (default: False)

    Returns:
        Dictionary with translated text and metadata
    """
    service = TranslateService()
    try:
        translated_text, full_text = await service.translate(content, target_lang, prompt, refresh)
        return {
            "success": True,
            "translated_text": translated_text,
            "translated_full_text": full_text,
            "content": content,
            "target_lang": target_lang,
            "cached": not refresh,
        }
    finally:
        await service.close()


# Explain Tools
@mcp.tool
async def explain_text(
    content: str,
    prompt: str | None = None,
    refresh: bool = False,
) -> dict:
    """Explain Chinese text (words, idioms, sayings).

    Args:
        content: Chinese text to explain
        prompt: Custom prompt template (optional)
        refresh: If True, bypass cache and regenerate (default: False)

    Returns:
        Dictionary with explained text and metadata
    """
    service = ExplainService()
    try:
        explained_text, full_text = await service.explain(content, prompt, refresh)
        return {
            "success": True,
            "explained_text": explained_text,
            "explained_full_text": full_text,
            "content": content,
            "cached": not refresh,
        }
    finally:
        await service.close()


# Practise Tools
@mcp.tool
async def generate_practise(
    topic: str,
    count: int = 5,
    types: str = "single_choice,multiple_choice,true_false",
    prompt: str | None = None,
    refresh: bool = False,
) -> dict:
    """Generate practise questions based on a topic.

    Args:
        topic: The topic/theme for generating questions
        count: Number of questions to generate (default: 5)
        types: Comma-separated question types:
               - single_choice (单选题)
               - multiple_choice (多选题)
               - true_false (判断题)
               (default: all types)
        prompt: Custom prompt template (optional)
        refresh: If True, bypass cache and regenerate (default: False)

    Returns:
        Dictionary with generated questions and metadata
    """
    type_list = [t.strip() for t in types.split(",") if t.strip()]
    service = PractiseService()
    try:
        questions, full_text = await service.generate_practise(topic, count, type_list, prompt, refresh)
        return {
            "success": True,
            "topic": topic,
            "count": len(questions),
            "total_requested": count,
            "types": type_list,
            "questions": questions,
            "practise_full_text": full_text,
            "cached": not refresh,
        }
    finally:
        await service.close()
