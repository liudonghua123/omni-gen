# omni-gen

AI Generation API Server with REST and MCP support.

## Features

- **Text-to-Speech (TTS)**: Convert text to audio files (WAV/MP3)
- **Image Generation**: Generate images from text prompts
- **Speech-to-Text (ASR)**: Transcribe audio to text

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Run server
uv run python run.py
```

## API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tts` | POST | Generate speech from text |
| `/api/v1/tts/{text}.{wav\|mp3}` | GET | Simple TTS route |
| `/api/v1/image` | POST | Generate image from prompt |
| `/api/v1/asr` | POST | Transcribe audio to text |
| `/health` | GET | Health check |

### MCP

| Endpoint | Description |
|----------|-------------|
| `/mcp` | MCP server endpoint |

## Configuration

Configure API keys in `.env`:

```env
TTS_API_KEY=your-tts-api-key
IMAGE_API_KEY=your-image-api-key
ASR_API_KEY=your-asr-api-key
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run in development mode
uv run python run.py

# Lint
uv run ruff check .
```