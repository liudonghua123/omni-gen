# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`omni-gen` is an AI Generation API Server that provides Text-to-Speech (TTS), Image Generation, and Speech-to-Text (ASR) capabilities through both REST API and MCP (Model Context Protocol) interfaces.

## Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run the server
uv run python run.py

# Lint code
uv run ruff check .
```

## Architecture

```
omni_gen/
├── main.py          # FastAPI app entry point, MCP server integration
├── routes.py        # REST API endpoints (/api/v1/*)
├── mcp_tools.py     # MCP tool definitions using FastMCP
├── config.py        # Pydantic Settings from .env
├── cache.py         # Cache management
├── services/        # Service layer for TTS, Image, ASR
│   ├── tts.py       # Text-to-Speech service
│   ├── image.py     # Image generation service
│   └── asr.py       # Speech-to-text service
└── static/          # Frontend test page
    └── index.html   # Interactive API test UI

run.py               # Entry point that runs uvicorn
```

**Key Integration Points:**
- FastAPI serves REST API routes + mounts MCP at `/mcp`
- Services use httpx to call external AI APIs (configured via environment)
- Cache directory stores generated files, served via `/api/v1/cache/*`

## API Structure

| Interface | Base Path | Description |
|-----------|-----------|-------------|
| REST | `/api/v1/` | TTS, Image, ASR endpoints |
| MCP | `/mcp` | JSON-RPC tools for AI clients |
| Static | `/static/` | Frontend assets |

## Configuration

Configure via `.env` file (copy from `.env.example`):
- Server: `HOST`, `PORT`, `DEBUG`
- Paths: `CACHE_DIR`
- API keys and base URLs for TTS, Image, and ASR services

## Static Test Page

The frontend test UI at `/` (index.html) includes:
- Simple URL generation (text-hyphenated paths)
- REST API form testing
- MCP tool invocation

**Common JS Error Pattern**: When modifying this page, ensure all JavaScript code stays within a single `<script>` block before `</body>`. Duplicate code or code after the closing script tag will render as visible text.