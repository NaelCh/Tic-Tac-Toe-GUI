"""Read the same release version used by the installer and build workflow."""
from pathlib import Path

VERSION = Path(__file__).resolve().with_name('VERSION').read_text(encoding='utf-8').strip()
