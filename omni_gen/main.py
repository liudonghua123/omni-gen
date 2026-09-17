#!/usr/bin/env python3
"""Main FastAPI application for omni-gen with MCP support."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from omni_gen.config import get_settings
from omni_gen.mcp_tools import mcp
from omni_gen.routes import router as api_router, simple_router

# Create ASGI app from MCP server (streamable-http stateless transport)
mcp_app = mcp.http_app(
    path="/mcp",
    transport="streamable-http",
    stateless_http=True,  # Stateless mode - each request is independent
)

# Create FastAPI app with MCP lifespan
app = FastAPI(
    title="omni-gen API",
    description="AI Generation API Server with REST and MCP support",
    version="0.1.0",
    lifespan=mcp_app.lifespan,  # Key: pass lifespan to FastAPI
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount MCP server at /ai
app.mount("/ai", mcp_app)

# Include REST API routes
app.include_router(api_router)
app.include_router(simple_router)


@app.get("/explorer.html", response_class=HTMLResponse)
async def explorer_html():
    """Serve explorer.html directly."""
    static_path = Path(__file__).parent.parent / "static"
    return (static_path / "explorer.html").read_text(encoding="utf-8")


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint - return server status info."""
    return {
        "name": "omni-gen",
        "version": "0.1.0",
        "description": "AI Generation API Server with REST and MCP support",
        "endpoints": {
            "api": "/api/v1",
            "simple": "/",
            "mcp": "/ai/mcp",
            "explorer": "/explorer.html",
            "health": "/api/v1/health",
        },
        "services": {
            "tts": {"endpoint": "/api/v1/tts", "method": "POST"},
            "tts_simple": {"endpoint": "/tts/{text}.{format}", "method": "GET"},
            "image": {"endpoint": "/api/v1/image", "method": "POST"},
            "image_simple": {"endpoint": "/image/{prompt}.{ext}", "method": "GET"},
            "asr": {"endpoint": "/api/v1/asr", "method": "POST"},
        },
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "omni_gen.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )