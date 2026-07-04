"""Arduino JSON response models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Type, TypeVar


@dataclass(frozen=True)
class ArduinoResponse:
    status: str
    command: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReadResponse(ArduinoResponse):
    soil_moisture_raw: int
    soil_moisture_percent: float
    is_wet: bool

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReadResponse":
        return cls(
            status=str(payload["status"]),
            command=str(payload["command"]),
            soil_moisture_raw=int(payload["soil_moisture_raw"]),
            soil_moisture_percent=float(payload["soil_moisture_percent"]),
            is_wet=bool(payload["is_wet"]),
        )


@dataclass(frozen=True)
class StatusResponse(ArduinoResponse):
    uptime_ms: int
    valve_open: bool
    dry_run: bool
    daily_watered_ms: int
    max_single_water_ms: int
    max_daily_water_ms: int
    wet_reject_percent: float
    soil_moisture_raw: int
    soil_moisture_percent: float
    is_wet: bool

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "StatusResponse":
        return cls(
            status=str(payload["status"]),
            command=str(payload["command"]),
            uptime_ms=int(payload["uptime_ms"]),
            valve_open=bool(payload["valve_open"]),
            dry_run=bool(payload["dry_run"]),
            daily_watered_ms=int(payload["daily_watered_ms"]),
            max_single_water_ms=int(payload["max_single_water_ms"]),
            max_daily_water_ms=int(payload["max_daily_water_ms"]),
            wet_reject_percent=float(payload["wet_reject_percent"]),
            soil_moisture_raw=int(payload["soil_moisture_raw"]),
            soil_moisture_percent=float(payload["soil_moisture_percent"]),
            is_wet=bool(payload["is_wet"]),
        )


@dataclass(frozen=True)
class CloseResponse(ArduinoResponse):
    valve_open: bool
    message: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CloseResponse":
        return cls(
            status=str(payload["status"]),
            command=str(payload["command"]),
            valve_open=bool(payload["valve_open"]),
            message=str(payload["message"]),
        )


@dataclass(frozen=True)
class ErrorResponse(ArduinoResponse):
    reason: str
    valve_open: bool
    message: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ErrorResponse":
        return cls(
            status=str(payload["status"]),
            command=str(payload["command"]),
            reason=str(payload["reason"]),
            valve_open=bool(payload["valve_open"]),
            message=str(payload["message"]),
        )


ResponseType = TypeVar("ResponseType", bound=ArduinoResponse)


def parse_response(payload: Mapping[str, Any], model_cls: Type[ResponseType]) -> ResponseType:
    if payload.get("status") in {"error", "rejected_by_safety"}:
        error = ErrorResponse.from_dict(payload)
        raise ValueError(f"Arduino returned {error.status}: {error.reason}")
    return model_cls.from_dict(payload)
