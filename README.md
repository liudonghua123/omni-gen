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
| `/api/v1/image` | POST | Generate image from prompt |
| `/api/v1/asr` | POST | Transcribe audio to text |
| `/api/v1/health` | GET | Health check |

### Simple Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts/{text}.{wav\|mp3}` | GET | Simple TTS route |
| `/image/{prompt}.png` | GET | Simple image route |
| `/cache/{path}` | GET | Serve cached files |

### MCP

| Endpoint | Description |
|----------|-------------|
| `/ai/mcp` | MCP server endpoint |

### Pages

| Endpoint | Description |
|----------|-------------|
| `/` | Server status info (JSON) |
| `/explorer.html` | Interactive API explorer |

## Configuration

Configure in `.env`:

```env
# Server
HOST=0.0.0.0
PORT=8000
APP_BASE_URL=http://localhost:8000

# API Keys
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