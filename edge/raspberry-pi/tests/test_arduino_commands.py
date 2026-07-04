from __future__ import annotations

from app.models.arduino_response import CloseResponse, ReadResponse, StatusResponse


def test_read_response_parse() -> None:
    payload = {
        "status": "ok",
        "command": "read",
        "soil_moisture_raw": 472,
        "soil_moisture_percent": 0.0,
        "is_wet": False,
    }
    response = ReadResponse.from_dict(payload)
    assert response.command == "read"
    assert response.soil_moisture_raw == 472


def test_status_response_parse() -> None:
    payload = {
        "status": "ok",
        "command": "status",
        "uptime_ms": 17911,
        "valve_open": False,
        "dry_run": True,
        "daily_watered_ms": 0,
        "max_single_water_ms": 5000,
        "max_daily_water_ms": 30000,
        "wet_reject_percent": 75.0,
        "soil_moisture_raw": 472,
        "soil_moisture_percent": 0.0,
        "is_wet": False,
    }
    response = StatusResponse.from_dict(payload)
    assert response.command == "status"
    assert response.daily_watered_ms == 0


def test_close_response_parse() -> None:
    payload = {
        "status": "ok",
        "command": "close",
        "valve_open": False,
        "message": "valve_closed",
    }
    response = CloseResponse.from_dict(payload)
    assert response.message == "valve_closed"
