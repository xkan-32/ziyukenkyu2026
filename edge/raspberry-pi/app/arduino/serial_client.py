"""Arduino serial client."""

from __future__ import annotations

import json
import time
from json import JSONDecodeError
from typing import Any, Dict, Optional, Protocol

import serial

from app.arduino.mock_serial import MockSerialTransport
from app.config import Settings


class SerialTransport(Protocol):
    def open(self) -> None:
        ...

    def close(self) -> None:
        ...

    def send_command(self, command: str) -> Dict[str, Any]:
        ...


class SerialClientError(RuntimeError):
    """Base serial client error."""


class SerialTimeoutError(SerialClientError):
    """Raised when the Arduino does not respond in time."""


class SerialParseError(SerialClientError):
    """Raised when a response cannot be parsed as JSON."""


class PySerialTransport:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._serial: Optional[serial.Serial] = None

    def open(self) -> None:
        if self._serial is None:
            self._serial = serial.Serial(
                self.settings.arduino_serial_port,
                self.settings.arduino_baud_rate,
                timeout=self.settings.serial_read_timeout_seconds,
                write_timeout=self.settings.serial_command_timeout_seconds,
            )
            self._flush_boot_lines()

    def _flush_boot_lines(self) -> None:
        assert self._serial is not None
        self._serial.reset_input_buffer()
        time.sleep(0.1)
        while self._serial.in_waiting:
            self._serial.readline()

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def send_command(self, command: str) -> Dict[str, Any]:
        self.open()
        assert self._serial is not None
        self._serial.write(f"{command.strip()}\n".encode("utf-8"))
        self._serial.flush()
        return self._read_response_json()

    def _read_response_json(self, *, max_attempts: int = 5) -> Dict[str, Any]:
        assert self._serial is not None
        for _ in range(max_attempts):
            raw_line = self._serial.readline()
            if not raw_line:
                break
            try:
                payload = json.loads(raw_line.decode("utf-8").strip())
            except (UnicodeDecodeError, JSONDecodeError) as exc:
                raise SerialParseError(str(exc)) from exc
            if payload.get("command") == "boot":
                continue
            return payload
        raise SerialTimeoutError("No usable JSON response from Arduino")


class SerialClient:
    def __init__(
        self,
        settings: Settings,
        transport: Optional[SerialTransport] = None,
    ) -> None:
        self.settings = settings
        self.transport = transport or self._build_transport()

    def _build_transport(self) -> SerialTransport:
        if self.settings.dry_run_mode:
            return MockSerialTransport()
        return PySerialTransport(self.settings)

    def open(self) -> "SerialClient":
        self.transport.open()
        return self

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> "SerialClient":
        return self.open()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def send_command(self, command: str) -> Dict[str, Any]:
        return self.transport.send_command(command)
