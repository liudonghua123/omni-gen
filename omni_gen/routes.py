"""REST API routes for omni-gen."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from omni_gen.config import get_settings
from omni_gen.services import ASRService, ExplainService, ImageService, TTSService, TranslateService

router = APIRouter(prefix="/api/v1")

# Simple routes without /api/v1 prefix
simple_router = APIRouter()


def get_base_url() -> str:
    """Get the base URL from settings."""
    settings = get_settings()
    return settings.app_base_url.replace("\\", "/")


# Request/Response models
class TTSRequest(BaseModel):
    text: str
    format: Optional[str] = None


class TTSResponse(BaseModel):
    success: bool
    file_path: str
    format: str
    size_bytes: int


class ImageRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"


class ImageResponse(BaseModel):
    success: bool
    file_path: str
    size: str
    width: int
    height: int


class ASRResponse(BaseModel):
    success: bool
    text: str
    language: str


class TranslateRequest(BaseModel):
    text: str
    target_lang: Optional[str] = None


class TranslateResponse(BaseModel):
    success: bool
    translated_text: str
    translated_full_text: str
    source_text: str
    target_lang: str


class ExplainResponse(BaseModel):
    success: bool
    explained_text: str
    explained_full_text: str
    source_text: str


# TTS Routes
@router.post("/tts", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Generate speech from text (REST API)."""
    service = TTSService()
    try:
        audio_bytes, path = await service.synthesize(request.text, request.format)
        base_url = get_base_url()
        relative_path = path.relative_to(get_settings().cache_dir).as_posix()
        return TTSResponse(
            success=True,
            file_path=f"{base_url}/cache/{relative_path}",
            format=request.format or "wav",
            size_bytes=len(audio_bytes),
        )
    finally:
        await service.close()


# Simple path-based TTS route: /tts/你好，世界！.wav
@simple_router.get("/tts/{text_and_format:path}")
async def synthesize_simple(text_and_format: str):
    """Simple TTS route: /tts/text.format"""
    # Parse text and format from path
    if "." not in text_and_format:
        raise HTTPException(status_code=400, detail="Format must be specified (e.g., .wav or .mp3)")

    text, fmt = text_and_format.rsplit(".", 1)
    text = text.replace("/", " ")  # URL decode space
    fmt = fmt.lower()

    if fmt not in ("wav", "mp3"):
        raise HTTPException(status_code=400, detail="Supported formats: wav, mp3")

    service = TTSService()
    try:
        audio_bytes, path = await service.synthesize(text, fmt)

        media_type = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
        }[fmt]

        # Use filename for download, no filename for inline preview
        return FileResponse(
            path=str(path),
            media_type=media_type,
        )
    finally:
        await service.close()


# Simple translate route: /translate/hello?target_lang=zh_CN (returns plain text)
@simple_router.get("/translate/{text}")
async def translate_simple(text: str, target_lang: str | None = None):
    """Simple translate route: /translate/text?target_lang=xx_XX

    Returns plain text translation.
    """
    service = TranslateService()
    try:
        translated_text, _ = await service.translate(text, target_lang)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(translated_text)
    finally:
        await service.close()


# Image Generation Routes
@router.post("/image", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """Generate image from text (REST API)."""
    service = ImageService()
    try:
        image_bytes, path = await service.generate(
            request.prompt, request.size, request.quality
        )
        base_url = get_base_url()
        relative_path = path.relative_to(get_settings().cache_dir).as_posix()
        return ImageResponse(
            success=True,
            file_path=f"{base_url}/cache/{relative_path}",
            size=request.size,
            width=int(request.size.split("x")[0]),
            height=int(request.size.split("x")[1]),
        )
    finally:
        await service.close()


# Simple path-based image route: /image/a beautiful sunset.png
@simple_router.get("/image/{prompt_and_ext:path}")
async def generate_image_simple(prompt_and_ext: str):
    """Simple image route: /image/prompt.png"""
    # Note: This is a simplified version; in practice, you'd URL-encode the prompt
    if "." not in prompt_and_ext:
        raise HTTPException(status_code=400, detail="Extension must be specified")

    prompt, ext = prompt_and_ext.rsplit(".", 1)
    prompt = prompt.replace("-", " ")  # Hyphens to spaces

    service = ImageService()
    try:
        image_bytes, path = await service.generate(prompt)
        # No filename = inline display in browser instead of download
        return FileResponse(
            path=str(path),
            media_type="image/png",
        )
    finally:
        await service.close()


# ASR Routes
@router.post("/asr", response_model=ASRResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = "",
):
    """Transcribe audio to text (REST API)."""
    audio_bytes = await file.read()

    service = ASRService()
    try:
        text, path = await service.transcribe(
            audio_bytes, file.filename or "audio.wav", language
        )
        return ASRResponse(
            success=True,
            text=text,
            language=language or "auto",
        )
    finally:
        await service.close()


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "omni-gen"}


# Translate Routes
@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text using AI (REST API)."""
    service = TranslateService()
    try:
        translated_text, full_text = await service.translate(request.text, request.target_lang)
        settings = get_settings()
        return TranslateResponse(
            success=True,
            translated_text=translated_text,
            translated_full_text=full_text,
            source_text=request.text,
            target_lang=request.target_lang or settings.translate_default_target_lang,
        )
    finally:
        await service.close()


# Explain Routes
@router.post("/explain", response_model=ExplainResponse)
async def explain_text(request: TranslateRequest):
    """Explain Chinese text (words, idioms, sayings) using AI."""
    service = ExplainService()
    try:
        explained_text, full_text = await service.explain(request.text)
        return ExplainResponse(
            success=True,
            explained_text=explained_text,
            explained_full_text=full_text,
            source_text=request.text,
        )
    finally:
        await service.close()


# Simple explain route: /explain/hello (returns plain text)
@simple_router.get("/explain/{text}")
async def explain_simple(text: str):
    """Simple explain route: /explain/text

    Returns plain text explanation.
    """
    service = ExplainService()
    try:
        explained_text, _ = await service.explain(text)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(explained_text)
    finally:
        await service.close()


# Cache file serving routes (no /api/v1 prefix for cleaner URLs)
@simple_router.get("/cache/{filename:path}")
async def serve_cache_file(filename: str):
    """Serve cached files for preview.

    Args:
        filename: Relative path to cached file (e.g., 'audio/xxx.mp3')

    Returns:
        FileResponse with appropriate media type
    """
    settings = get_settings()
    cache_path = settings.cache_dir / filename

    # Security check: prevent path traversal
    if ".." in filename:
        raise HTTPException(status_code=403, detail="Invalid path")

    # Check if resolved path is within cache directory
    try:
        cache_path = cache_path.resolve()
        base_path = settings.cache_dir.resolve()
        if cache_path.is_relative_to(base_path):
            pass  # Safe path
        else:
            raise HTTPException(status_code=403, detail="Invalid path")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not cache_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    ext = cache_path.suffix.lower()
    media_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(cache_path),
        media_type=media_type,
        filename=cache_path.name,
    )


__all__ = ["router", "simple_router"]
