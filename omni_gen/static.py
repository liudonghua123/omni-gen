"""Static files and templates for omni-gen."""

from pathlib import Path

# Path to static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)