"""MCP tools for omni-gen services."""

from fastmcp import FastMCP

from omni_gen.config import get_settings
from omni_gen.services import ASRService, ExplainService, ImageService, TTSService, TranslateService

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
    text: str,
    target_lang: str | None = None
) -> dict:
    """Translate text to target language.

    Args:
        text: Text to translate
        target_lang: Target language code (e.g., "en_US", "zh_CN")

    Returns:
        Dictionary with translated text and metadata
    """
    service = TranslateService()
    try:
        translated_text, full_text = await service.translate(text, target_lang)
        return {
            "success": True,
            "translated_text": translated_text,
            "translated_full_text": full_text,
            "source_text": text,
            "target_lang": target_lang or get_settings().translate_default_target_lang,
        }
    finally:
        await service.close()


# Explain Tools
@mcp.tool
async def explain_text(text: str) -> dict:
    """Explain Chinese text (words, idioms, sayings).

    Args:
        text: Chinese text to explain

    Returns:
        Dictionary with explained text and metadata
    """
    service = ExplainService()
    try:
        explained_text, full_text = await service.explain(text)
        return {
            "success": True,
            "explained_text": explained_text,
            "explained_full_text": full_text,
            "source_text": text,
        }
    finally:
        await service.close()