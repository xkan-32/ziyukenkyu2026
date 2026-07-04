"""Local queue record."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LocalQueueRecord:
    id: str
    created_at: str
    payload_type: str
    payload: Dict[str, Any]
    status: str = "queued"
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
