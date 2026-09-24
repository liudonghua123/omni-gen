# omni-gen

AI Generation API Server with REST and MCP support.

## Features

- **Text-to-Speech (TTS)**: Convert text to audio files (WAV/MP3)
- **Image Generation**: Generate images from text prompts
- **Speech-to-Text (ASR)**: Transcribe audio to text
- **Translate**: Translate text using AI models
- **Explain**: Explain Chinese words, idioms, sayings

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
| `/api/v1/translate` | POST | Translate text |
| `/api/v1/explain` | POST | Explain Chinese words/idioms |
| `/api/v1/health` | GET | Health check |

### Simple Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tts/{text}.{wav\|mp3}` | GET | Simple TTS route |
| `/image/{prompt}.png` | GET | Simple image route |
| `/translate/{text}?target_lang=xx_XX` | GET | Simple translate route |
| `/explain/{text}` | GET | Simple explain route |
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

# OpenAI (Generic AI)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# TTS
TTS_BASE_URL=https://new-api.app.ynu.edu.cn/v1
TTS_API_KEY=sk-your-tts-api-key
TTS_MODEL=bosonai/higgs-audio-v3-tts-4b

# Image Generation
IMAGE_BASE_URL=https://new-api.app.ynu.edu.cn/v1
IMAGE_API_KEY=sk-your-image-api-key
IMAGE_MODEL=dall-e-3

# ASR
ASR_BASE_URL=https://new-api.app.ynu.edu.cn/v1
ASR_API_KEY=sk-your-asr-api-key
ASR_MODEL=whisper-1

# Translate (falls back to OpenAI if not configured)
TRANSLATE_BASE_URL=https://api.openai.com/v1
TRANSLATE_API_KEY=sk-your-translate-api-key
TRANSLATE_MODEL=gpt-4o-mini
TRANSLATE_DEFAULT_TARGET_LANG=en_US
TRANSLATE_PROMPT=Translate the following text into {target_lang}. Note that you should only output the translated result without any additional explanation:

{content}

# Explain (Chinese words, idioms, sayings)
EXPLAIN_BASE_URL=https://api.openai.com/v1
EXPLAIN_API_KEY=sk-your-explain-api-key
EXPLAIN_MODEL=gpt-4o-mini
EXPLAIN_PROMPT=请解释以下中文词语、成语或歇后语，包括其中文含义、英文翻译、以及在句子中的用法示例。注意只输出解释内容，不要有其他说明：

{content}
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