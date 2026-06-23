"""アプリケーション設定."""

import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
VERTEX_AI_LOCATION: str = os.getenv("VERTEX_AI_LOCATION", "asia-northeast1")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
