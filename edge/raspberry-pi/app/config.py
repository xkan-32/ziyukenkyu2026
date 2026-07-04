"""Raspberry Pi observation settings."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    arduino_serial_port: str = "/dev/ttyACM0"
    arduino_baud_rate: int = 115200
    allow_water_command_from_pi: bool = False
    dry_run_mode: bool = True
    camera_enabled: bool = True
    experiment_round_id: str = "round_1"
    planter_profile_id: str = "ai_planter_a"
    local_data_dir: Path = Path("./data/local")
    observation_interval_minutes: int = 60
    gcp_project_id: str = ""
    gcs_bucket_name: str = ""
    agent_api_url: str = ""
    log_level: str = "INFO"
    serial_read_timeout_seconds: float = 3.0
    serial_command_timeout_seconds: float = 5.0

    @classmethod
    def from_env(cls, *, force_dry_run: bool = False) -> "Settings":
        dry_run_mode = _get_bool("DRY_RUN_MODE", True)
        if force_dry_run:
            dry_run_mode = True

        return cls(
            arduino_serial_port=os.getenv("ARDUINO_SERIAL_PORT", "/dev/ttyACM0"),
            arduino_baud_rate=int(os.getenv("ARDUINO_BAUD_RATE", "115200")),
            allow_water_command_from_pi=_get_bool(
                "ALLOW_WATER_COMMAND_FROM_PI",
                False,
            ),
            dry_run_mode=dry_run_mode,
            camera_enabled=_get_bool("CAMERA_ENABLED", True),
            experiment_round_id=os.getenv("EXPERIMENT_ROUND_ID", "round_1"),
            planter_profile_id=os.getenv("PLANTER_PROFILE_ID", "ai_planter_a"),
            local_data_dir=Path(os.getenv("LOCAL_DATA_DIR", "./data/local")),
            observation_interval_minutes=int(
                os.getenv("OBSERVATION_INTERVAL_MINUTES", "60")
            ),
            gcp_project_id=os.getenv("GCP_PROJECT_ID", ""),
            gcs_bucket_name=os.getenv("GCS_BUCKET_NAME", ""),
            agent_api_url=os.getenv("AGENT_API_URL", ""),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
