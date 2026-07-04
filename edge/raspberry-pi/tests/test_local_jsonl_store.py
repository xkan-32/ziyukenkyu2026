from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.local_queue import LocalQueueRecord
from app.models.observation import ObservationRecord, SoilMoistureReading
from app.storage.local_jsonl_store import LocalJsonlStore

JST = ZoneInfo("Asia/Tokyo")


def test_append_and_read_jsonl(tmp_path) -> None:
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=JST)
    store = LocalJsonlStore(tmp_path)

    observation = ObservationRecord(
        id="obs_20260704_120000_ai_planter_a",
        experiment_round_id="round_1",
        planter_profile_id="ai_planter_a",
        observed_at=observed_at.isoformat(),
        observation_type="scheduled",
        soil_moisture_raw=472,
        soil_moisture_percent=0.0,
        image_local_path=None,
        thumbnail_local_path=None,
        image_gcs_path=None,
        thumbnail_gcs_path=None,
        weather_summary=None,
        source="raspberry_pi",
        device_status="ok",
        arduino_status_response=None,
    )
    reading = SoilMoistureReading(
        id="smr_20260704_120000_ai_planter_a",
        experiment_round_id="round_1",
        planter_profile_id="ai_planter_a",
        read_at=observed_at.isoformat(),
        watering_event_id=None,
        measurement_phase="normal_periodic",
        sequence_no=1,
        minutes_after_watering=None,
        soil_moisture_raw=472,
        soil_moisture_percent=0.0,
        source="raspberry_pi",
    )
    queue_record = LocalQueueRecord(
        id="queue_obs_20260704_120000_ai_planter_a",
        created_at=observed_at.isoformat(),
        payload_type="observation",
        payload=observation.to_dict(),
    )

    store.append_observation(observation)
    store.append_soil_reading(reading)
    store.enqueue_for_sync(queue_record)

    assert len(store.read_records(store.observations_path)) == 1
    assert len(store.read_records(store.soil_readings_path)) == 1
    assert len(store.read_records(store.queue_path)) == 1
