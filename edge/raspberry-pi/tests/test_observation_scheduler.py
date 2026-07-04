from __future__ import annotations

from app.scheduler.observation_scheduler import run_observation_cycle
from app.storage.local_jsonl_store import LocalJsonlStore


def test_run_observation_cycle_persists_records(settings) -> None:
    observation = run_observation_cycle(settings)
    store = LocalJsonlStore(settings.local_data_dir)

    observations = store.read_records(store.observations_path)
    soil_readings = store.read_records(store.soil_readings_path)
    queue_records = store.read_records(store.queue_path)

    assert observation.device_status == "ok"
    assert len(observations) == 1
    assert len(soil_readings) == 1
    assert len(queue_records) == 1
    assert observations[0]["id"] == observation.id
