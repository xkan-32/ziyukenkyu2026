"""Observation and moisture reading records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ObservationRecord:
    id: str
    experiment_round_id: str
    planter_profile_id: str
    observed_at: str
    observation_type: str
    soil_moisture_raw: Optional[int]
    soil_moisture_percent: Optional[float]
    image_local_path: Optional[str]
    thumbnail_local_path: Optional[str]
    image_gcs_path: Optional[str]
    thumbnail_gcs_path: Optional[str]
    weather_summary: Optional[str]
    source: str
    device_status: str
    arduino_status_response: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def build_id(observed_at: datetime, planter_profile_id: str) -> str:
        return (
            f"obs_{observed_at.strftime('%Y%m%d_%H%M%S_%f')}_{planter_profile_id}"
        )


@dataclass(frozen=True)
class SoilMoistureReading:
    id: str
    experiment_round_id: str
    planter_profile_id: str
    read_at: str
    watering_event_id: Optional[str]
    measurement_phase: str
    sequence_no: int
    minutes_after_watering: Optional[int]
    soil_moisture_raw: Optional[int]
    soil_moisture_percent: Optional[float]
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def build_id(read_at: datetime, planter_profile_id: str) -> str:
        return f"smr_{read_at.strftime('%Y%m%d_%H%M%S_%f')}_{planter_profile_id}"
