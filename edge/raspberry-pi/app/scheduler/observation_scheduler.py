"""Normal observation flow."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from app.arduino.commands import ArduinoCommandClient
from app.arduino.serial_client import SerialClient, SerialClientError
from app.camera.capture import capture_image
from app.camera.image_resize import create_thumbnail
from app.config import Settings
from app.gcp.firestore_sync import sync_observation
from app.gcp.storage_upload import upload_image
from app.models.local_queue import LocalQueueRecord
from app.models.observation import ObservationRecord, SoilMoistureReading
from app.storage.local_jsonl_store import LocalJsonlStore
from app.storage.local_queue_store import LocalQueueStore

logger = logging.getLogger(__name__)

JST = ZoneInfo("Asia/Tokyo")


def _store_path(path: Optional[Path], base_dir: Path) -> Optional[str]:
    if path is None:
        return None
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(base_dir.resolve()))
    except ValueError:
        return str(resolved)


def run_observation_cycle(
    settings: Settings,
    *,
    serial_client: Optional[SerialClient] = None,
    store: Optional[LocalJsonlStore] = None,
) -> ObservationRecord:
    observed_at = datetime.now(JST)
    local_store = store or LocalJsonlStore(settings.local_data_dir)
    queue_store = LocalQueueStore(local_store)

    arduino_status = None
    close_failed = False
    device_status = "ok"
    read_response = None

    active_serial_client = serial_client or SerialClient(settings)
    with active_serial_client as opened_client:
        command_client = ArduinoCommandClient(opened_client)
        try:
            command_client.close_valve()
        except SerialClientError as exc:
            close_failed = True
            device_status = "partial"
            logger.warning("Failed to close valve before observation: %s", exc)

        try:
            read_response = command_client.read_moisture()
            arduino_status = command_client.get_status().to_dict()
        except (SerialClientError, ValueError) as exc:
            device_status = "device_error"
            logger.exception("Observation failed to read Arduino state: %s", exc)

    image_path = capture_image(settings, observed_at)
    thumbnail_path = create_thumbnail(image_path) if image_path is not None else None
    image_gcs_path = upload_image(image_path, settings)
    thumbnail_gcs_path = upload_image(thumbnail_path, settings)

    observation = ObservationRecord(
        id=ObservationRecord.build_id(observed_at, settings.planter_profile_id),
        experiment_round_id=settings.experiment_round_id,
        planter_profile_id=settings.planter_profile_id,
        observed_at=observed_at.isoformat(),
        observation_type="scheduled",
        soil_moisture_raw=getattr(read_response, "soil_moisture_raw", None),
        soil_moisture_percent=getattr(read_response, "soil_moisture_percent", None),
        image_local_path=_store_path(image_path, settings.local_data_dir),
        thumbnail_local_path=_store_path(thumbnail_path, settings.local_data_dir),
        image_gcs_path=image_gcs_path,
        thumbnail_gcs_path=thumbnail_gcs_path,
        weather_summary=None,
        source="raspberry_pi",
        device_status=device_status,
        arduino_status_response=arduino_status,
    )
    local_store.append_observation(observation)

    reading = SoilMoistureReading(
        id=SoilMoistureReading.build_id(observed_at, settings.planter_profile_id),
        experiment_round_id=settings.experiment_round_id,
        planter_profile_id=settings.planter_profile_id,
        read_at=observed_at.isoformat(),
        watering_event_id=None,
        measurement_phase="normal_periodic",
        sequence_no=1,
        minutes_after_watering=None,
        soil_moisture_raw=observation.soil_moisture_raw,
        soil_moisture_percent=observation.soil_moisture_percent,
        source="raspberry_pi",
    )
    local_store.append_soil_reading(reading)

    sync_succeeded = sync_observation(observation, settings)
    if not sync_succeeded:
        queue_store.enqueue(
            LocalQueueRecord(
                id=f"queue_{observation.id}",
                created_at=observed_at.isoformat(),
                payload_type="observation",
                payload=observation.to_dict(),
            )
        )

    return observation
