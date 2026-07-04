"""Typed Arduino command helpers."""

from __future__ import annotations

from app.arduino.serial_client import SerialClient
from app.models.arduino_response import CloseResponse, ReadResponse, StatusResponse, parse_response


class ArduinoCommandClient:
    def __init__(self, serial_client: SerialClient) -> None:
        self.serial_client = serial_client

    def read_moisture(self) -> ReadResponse:
        payload = self.serial_client.send_command("read")
        return parse_response(payload, ReadResponse)

    def get_status(self) -> StatusResponse:
        payload = self.serial_client.send_command("status")
        return parse_response(payload, StatusResponse)

    def close_valve(self) -> CloseResponse:
        payload = self.serial_client.send_command("close")
        return parse_response(payload, CloseResponse)
