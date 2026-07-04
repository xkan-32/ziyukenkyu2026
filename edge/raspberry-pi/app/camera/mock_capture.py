"""Mock image generation for dry runs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw


def create_mock_image(output_dir: Path, timestamp: datetime) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    image = Image.new("RGB", (1280, 960), color=(204, 230, 201))
    drawer = ImageDraw.Draw(image)
    drawer.text((40, 40), f"dry-run {timestamp.isoformat()}", fill=(20, 40, 20))
    image.save(file_path, format="JPEG", quality=90)
    return file_path
