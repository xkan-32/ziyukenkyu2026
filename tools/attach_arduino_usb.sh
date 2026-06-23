#!/usr/bin/env bash
# WSL2 から Arduino USB デバイスを接続する。
# 前提: Windows 側に usbipd-win がインストール済みであること。
set -euo pipefail

USBIPD="${USBIPD:-/mnt/c/Program Files/usbipd-win/usbipd.exe}"
USBIPD_WIN="$(wslpath -w "$USBIPD")"
ARDUINO_VID="${ARDUINO_VID:-2341}"

if [[ ! -f "$USBIPD" ]]; then
  echo "error: usbipd-win が見つかりません: $USBIPD" >&2
  echo "Windows PowerShell (管理者) で次を実行してください:" >&2
  echo "  winget install --id dorssel.usbipd-win" >&2
  exit 1
fi

list_output="$(powershell.exe -NoProfile -Command "& '$USBIPD_WIN' list" 2>&1)" || {
  echo "$list_output" >&2
  exit 1
}

busid="$(printf '%s\n' "$list_output" | awk -v vid="$ARDUINO_VID" '
  $0 ~ vid && $1 ~ /^[0-9]+-[0-9]+$/ { print $1; exit }
')"

if [[ -z "$busid" ]]; then
  echo "error: Arduino (VID ${ARDUINO_VID}) が usbipd list に見つかりません。" >&2
  echo "$list_output" >&2
  exit 1
fi

echo "Arduino BUSID: $busid"

# bind は管理者権限が必要。未共有なら管理者 PowerShell で bind を促す。
if printf '%s\n' "$list_output" | awk -v busid="$busid" '$1 == busid && /Not shared/ { found=1 } END { exit !found }'; then
  echo "デバイスは未共有です。管理者 PowerShell で次を実行してください:"
  echo "  usbipd bind --busid $busid"
  exit 1
fi

powershell.exe -NoProfile -Command "& '$USBIPD_WIN' attach --wsl --busid $busid" >/dev/null

for _ in $(seq 1 20); do
  if ls /dev/ttyACM* /dev/ttyUSB* >/dev/null 2>&1; then
    ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true
    exit 0
  fi
  sleep 0.5
done

echo "warning: USB は attach されましたが、シリアルデバイスがまだ見えません。" >&2
echo "  ls -l /dev/ttyACM* を確認してください。" >&2
exit 1
