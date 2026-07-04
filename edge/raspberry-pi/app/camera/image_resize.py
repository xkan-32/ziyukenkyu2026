"""Image resize helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def create_thumbnail(source_path: Path, max_edge: int = 640) -> Path:
    thumbnail_path = source_path.with_name(f"{source_path.stem}_small{source_path.suffix}")
    with Image.open(source_path) as image:
        image.thumbnail((max_edge, max_edge))
        image.save(thumbnail_path, format="JPEG", quality=85)
    return thumbnail_path
