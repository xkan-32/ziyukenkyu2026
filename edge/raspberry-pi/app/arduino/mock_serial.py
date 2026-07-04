"""Dry-run serial transport."""

from __future__ import annotations

from typing import Any, Dict


class MockSerialTransport:
    def __init__(self) -> None:
        self.is_open = False

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def send_command(self, command: str) -> Dict[str, Any]:
        normalized = command.strip()
        if normalized == "read":
            return {
                "status": "ok",
                "command": "read",
                "soil_moisture_raw": 472,
                "soil_moisture_percent": 0.0,
                "is_wet": False,
            }
        if normalized == "status":
            return {
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
        if normalized == "close":
            return {
                "status": "ok",
                "command": "close",
                "valve_open": False,
                "message": "valve_closed",
            }
        return {
            "status": "error",
            "command": "unknown",
            "reason": "unknown_command",
            "valve_open": False,
            "message": "rejected",
        }
