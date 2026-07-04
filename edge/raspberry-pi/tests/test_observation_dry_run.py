from __future__ import annotations

from app.arduino.commands import ArduinoCommandClient
from app.config import Settings
from app.scheduler.observation_scheduler import run_observation_cycle


def test_dry_run_keeps_water_disabled(settings) -> None:
    assert settings.allow_water_command_from_pi is False
    assert not hasattr(ArduinoCommandClient, "send_water_command")


def test_dry_run_cycle_uses_mocked_paths(settings) -> None:
    observation = run_observation_cycle(settings)
    assert observation.image_local_path is not None
    assert observation.image_local_path.endswith(".jpg")
    assert observation.image_gcs_path is None


def test_force_dry_run_overrides_env(tmp_path) -> None:
    settings = Settings.from_env(force_dry_run=True)
    assert settings.dry_run_mode is True
