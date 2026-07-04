"""Append-only JSONL storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.models.local_queue import LocalQueueRecord
from app.models.observation import ObservationRecord, SoilMoistureReading


class LocalJsonlStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.observations_path = self.root_dir / "observations.jsonl"
        self.soil_readings_path = self.root_dir / "soil_moisture_readings.jsonl"
        self.queue_path = self.root_dir / "local_queue.jsonl"

    def append_observation(self, observation: ObservationRecord) -> None:
        self._append_json(self.observations_path, observation.to_dict())

    def append_soil_reading(self, reading: SoilMoistureReading) -> None:
        self._append_json(self.soil_readings_path, reading.to_dict())

    def enqueue_for_sync(self, record: LocalQueueRecord) -> None:
        self._append_json(self.queue_path, record.to_dict())

    def read_records(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            return []
        return [
            json.loads(line)
            for line in file_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _append_json(self, file_path: Path, payload: Dict[str, Any]) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
