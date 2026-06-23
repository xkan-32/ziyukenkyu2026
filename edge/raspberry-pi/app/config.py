"""Raspberry Pi 設定."""

import os

from dotenv import load_dotenv

load_dotenv()

ARDUINO_SERIAL_PORT: str = os.getenv("ARDUINO_SERIAL_PORT", "/dev/ttyACM0")
ARDUINO_BAUD_RATE: int = int(os.getenv("ARDUINO_BAUD_RATE", "115200"))
GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
AGENT_API_URL: str = os.getenv("AGENT_API_URL", "")
CULTIVATION_GROUP: str = os.getenv("CULTIVATION_GROUP", "ai")
