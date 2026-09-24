#!/usr/bin/env python3
"""Entry point for omni-gen server."""

if __name__ == "__main__":
    import logging
    import sys

    import uvicorn

    from omni_gen.config import get_settings

    # Configure logging to show practise service logs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    settings = get_settings()
    uvicorn.run(
        "omni_gen.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
