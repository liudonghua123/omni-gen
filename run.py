#!/usr/bin/env python3
"""Entry point for omni-gen server."""

import sys

# Fix Windows console encoding to UTF-8 before any logging
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

import uvicorn
from omni_gen.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "omni_gen.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )