"""Firestore sync stub."""

from __future__ import annotations

import logging

from app.config import Settings
from app.models.observation import ObservationRecord

logger = logging.getLogger(__name__)


def sync_observation(observation: ObservationRecord, settings: Settings) -> bool:
    if not settings.gcp_project_id:
        logger.info("GCP project not configured; skipping Firestore sync")
        return False

    # TODO: Replace with google-cloud-firestore client write when credentials are available.
    logger.warning(
        "Firestore sync skeleton reached for %s but real sync is not implemented",
        observation.id,
    )
    return False
