"""Unused agent API stub for the observation-only phase."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.config import Settings

logger = logging.getLogger(__name__)


def request_judge(_payload: Dict[str, Any], settings: Settings) -> Optional[Dict[str, Any]]:
    if not settings.agent_api_url:
        logger.info("AGENT_API_URL not configured; judge API remains disabled")
        return None

    logger.warning("Judge API is intentionally not called during the observation-only phase")
    return None
