"""Camera capture helpers."""

from __future__ import annotations

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.camera.mock_capture import create_mock_image
from app.config import Settings

logger = logging.getLogger(__name__)


def capture_image(settings: Settings, observed_at: datetime) -> Optional[Path]:
    if not settings.camera_enabled:
        logger.info("Camera disabled; skipping capture")
        return None

    image_dir = settings.local_data_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    if settings.dry_run_mode:
        return create_mock_image(image_dir, observed_at)

    file_path = image_dir / f"{observed_at.strftime('%Y%m%d_%H%M%S')}.jpg"
    libcamera_still = shutil.which("libcamera-still")
    if libcamera_still is None:
        logger.warning("libcamera-still not available; falling back to mock image")
        return create_mock_image(image_dir, observed_at)

    try:
        subprocess.run(
            [libcamera_still, "-n", "-o", str(file_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        logger.warning("Camera capture failed; falling back to mock image: %s", exc)
        return create_mock_image(image_dir, observed_at)
    return file_path
