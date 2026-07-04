from __future__ import annotations

from typing import List

from app.arduino.commands import ArduinoCommandClient
from app.arduino.serial_client import PySerialTransport, SerialClient


class FakeSerial:
    def __init__(self, lines: List[bytes]) -> None:
        self._lines = list(lines)
        self.in_waiting = 0

    def readline(self) -> bytes:
        if not self._lines:
            return b""
        return self._lines.pop(0)

    def reset_input_buffer(self) -> None:
        self._lines.clear()


def test_mock_serial_read_status_close(settings) -> None:
    with SerialClient(settings) as serial_client:
        commands = ArduinoCommandClient(serial_client)
        close_response = commands.close_valve()
        read_response = commands.read_moisture()
        status_response = commands.get_status()

    assert close_response.valve_open is False
    assert read_response.command == "read"
    assert status_response.command == "status"


def test_pyserial_skips_boot_json(settings) -> None:
    transport = PySerialTransport(settings)
    transport._serial = FakeSerial(
        [
            b'{"status":"ready","command":"boot","valve_open":false,"message":"valve_closed_on_boot"}\n',
            b'{"status":"ok","command":"read","soil_moisture_raw":472,"soil_moisture_percent":0.0,"is_wet":false}\n',
        ]
    )
    payload = transport._read_response_json()
    assert payload["command"] == "read"
