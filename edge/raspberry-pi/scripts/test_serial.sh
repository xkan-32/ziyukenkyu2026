#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"
export DRY_RUN_MODE=true
export LOCAL_DATA_DIR="${LOCAL_DATA_DIR:-${ROOT_DIR}/data/local}"

python -m app.main --dry-run once
test -f "${LOCAL_DATA_DIR}/observations.jsonl"
test "$(wc -l < "${LOCAL_DATA_DIR}/observations.jsonl")" -ge 1
