from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        local_data_dir=tmp_path / "data" / "local",
        dry_run_mode=True,
        allow_water_command_from_pi=False,
    )
