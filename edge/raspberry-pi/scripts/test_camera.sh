#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"
export DRY_RUN_MODE=true
export LOCAL_DATA_DIR="${LOCAL_DATA_DIR:-${ROOT_DIR}/data/local}"

python -c "from datetime import datetime; from zoneinfo import ZoneInfo; from app.camera.capture import capture_image; from app.config import Settings; path = capture_image(Settings.from_env(force_dry_run=True), datetime.now(ZoneInfo('Asia/Tokyo'))); print(path)"
