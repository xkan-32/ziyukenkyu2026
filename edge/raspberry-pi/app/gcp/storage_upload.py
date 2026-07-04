"""Cloud Storage upload stub."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.config import Settings

logger = logging.getLogger(__name__)


def upload_image(file_path: Optional[Path], settings: Settings) -> Optional[str]:
    if file_path is None:
        return None
    if not settings.gcs_bucket_name:
        logger.info("GCS bucket not configured; skipping upload")
        return None

    # TODO: Replace with google-cloud-storage client upload when credentials are available.
    logger.warning("GCS upload skeleton reached for %s but real upload is not implemented", file_path)
    return None
