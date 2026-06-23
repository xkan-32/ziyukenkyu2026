#!/usr/bin/env bash
# WSL2 上で arduino-cli を使えるようにする初回セットアップ。
set -euo pipefail

BIN_DIR="${HOME}/bin"
INSTALL_SCRIPT="https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh"

echo "==> arduino-cli をインストール"
mkdir -p "$BIN_DIR"
if ! command -v arduino-cli >/dev/null 2>&1; then
  curl -fsSL "$INSTALL_SCRIPT" | BINDIR="$BIN_DIR" sh
fi

if ! grep -q 'HOME/bin' "${HOME}/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/bin:$PATH"' >> "${HOME}/.bashrc"
  echo "PATH を ~/.bashrc に追加しました"
fi
export PATH="$BIN_DIR:$PATH"

echo "==> arduino-cli バージョン"
arduino-cli version

echo "==> ボード定義をインストール (Arduino UNO R4 WiFi)"
arduino-cli config init --dest-dir "${HOME}/.arduino15" 2>/dev/null || true
arduino-cli core update-index
arduino-cli core install arduino:renesas_uno

echo "==> コンパイル確認"
make -C "$(dirname "$0")/../edge/arduino/valve_controller" compile

echo ""
echo "セットアップ完了。"
echo ""
echo "実機書き込みには Windows 側で usbipd-win が必要です。"
echo "管理者 PowerShell:"
echo "  winget install --id dorssel.usbipd-win"
echo "  usbipd list"
echo "  usbipd bind --busid <BUSID>   # Arduino の BUSID"
echo ""
echo "WSL から書き込み:"
echo "  make -C edge/arduino/valve_controller upload"
