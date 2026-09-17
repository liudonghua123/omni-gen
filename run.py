#!/usr/bin/env python3
"""Entry point for omni-gen server."""

if __name__ == "__main__":
    import uvicorn

    from omni_gen.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "omni_gen.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )