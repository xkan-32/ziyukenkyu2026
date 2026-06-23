# valve_controller

Arduino UNO R4 WiFi 向けの土壌水分センサー読み取り兼ソレノイドバルブ安全制御ファームウェアです。

## 役割

- 起動時に必ずバルブを閉じる
- 土壌水分の raw 値を読み、`config.h` の校正値から `%` に変換する
- `water <duration_ms>` を安全判定付きで実行する
- wet 判定、単回上限、24 時間累積上限を Arduino 単体で強制する
- すべてのシリアル応答を 1 行 JSON で返す

Arduino は「今、水をあげるべきか」は判断しません。
Arduino は Raspberry Pi / AI エージェントから `water <duration_ms>` 命令を受けたときに、安全に実行できるかだけを判定します。
土壌が乾燥していることは `water` 実行を許可しうる条件であり、自動水やりのトリガーではありません。
wet 判定、単回最大開放時間、1 日累積上限はすべて「安全拒否」のためのロジックです。

## 初期設定

[config.h](./config.h) を実機に合わせて更新します。

- `DRY_RUN_MODE`
  - `true` の間は実バルブを開かず、`TEST_LED_PIN` だけを点灯する
- `VALVE_PIN`
  - MOSFET モジュール制御入力へつなぐ Arduino GPIO
- `SOIL_MOISTURE_PIN`
  - 土壌水分センサーのアナログ入力
- `TEST_LED_PIN`
  - dry-run 時の疑似通水表示
- `SOIL_SENSOR_DRY_RAW`, `SOIL_SENSOR_WET_RAW`
  - センサー校正値
  - 現在は机上確認用の暫定値です。土壌へ実設置後に再校正してください
- `WET_REJECT_PERCENT`
  - この値以上なら `water` を拒否する
- `SENSOR_READ_SAMPLES`
  - 土壌水分の平均化サンプル数
- `SENSOR_READ_INTERVAL_MS`
  - サンプル間の待機時間
- `AFTER_WATER_READ_DELAY_MS`
  - `water` 応答用の `moisture_after` を読む前の待機時間
- `MAX_SINGLE_WATER_MS`
  - 1 回の最大通水時間
- `MAX_DAILY_WATER_MS`
  - 起動後 24 時間窓での累積通水上限

## コマンド

- `read`
- `status`
- `close`
- `water <duration_ms>`

例:

```text
read
status
close
water 3000
water    1000
```

`water` は引数の前後空白を許容しますが、`water` だけ、または `water    ` は `invalid_duration_ms` を返してバルブを閉じます。

## 配線例

### dry-run mode の配線

- Arduino UNO R4 WiFi 単体で動作確認できます
- `TEST_LED_PIN` は `LED_BUILTIN` を使います
- `DRY_RUN_MODE=true` の間は `VALVE_PIN` で実バルブを開きません
- `water 1000` で LED が 1 秒点灯します

### 土壌水分センサー配線

3 ピン土壌水分センサー想定です。

- センサー `VCC` -> Arduino `5V`
- センサー `GND` -> Arduino `GND`
- センサー `AO` / `AOUT` / `SIG` -> Arduino `A0`
- センサー `DO` がある場合、今回は使いません
- `config.h` の `SOIL_MOISTURE_PIN` と一致させます

### MOSFETモジュール制御側配線

- Arduino `VALVE_PIN`、現在 `D2` -> MOSFET モジュール `IN` / `SIG` / `PWM`
- Arduino `GND` -> MOSFET モジュール制御側 `GND`
- PWM 制御は使わず、ON/OFF のみ使います
- Arduino GPIO から 12V バルブを直接駆動してはいけません

### 12Vバルブ駆動側配線

MOSFET モジュールの端子名は商品や基板表記で異なる可能性があるため、以下は代表例です。

- `12V` 電源 `+` -> 電磁バルブ `+`
- 電磁バルブ `-` -> MOSFET モジュール `OUT-` / `LOAD-` / `V-`
- `12V` 電源 `-` -> MOSFET モジュール `VIN-` / `GND`
- 必要に応じて `12V` 電源 `+` -> MOSFET モジュール `VIN+` / `V+`

注意:

- 実際の基板表記を確認してから接続してください
- 12V 系と Arduino 5V 系を混同しないでください
- 制御 GND が必要なモジュールでは Arduino `GND` と制御 `GND` を共通にします
- ただし 12V の `+` を Arduino へ入れてはいけません

### フライバックダイオード

- 電磁バルブはコイル負荷なので OFF 時に逆起電力が出ます
- MOSFET モジュール上に保護ダイオードがあるか確認してください
- 無い場合は電磁バルブ両端に外付けフライバックダイオードを追加してください
- ダイオードのカソード、線がある側を 12V+ 側へ接続します
- ダイオードのアノード、線がない側を MOSFET 側 / バルブ- 側へ接続します

```text
12V+ ---- 電磁バルブ ---- MOSFET側
  |                         |
  +----|<|------------------+
       diode
       カソード(線あり)は12V+側
```

## 水回りの接続順

推奨順:

```text
給水元 -> 手動バルブ -> 流量調整バルブ -> 電磁バルブ -> チューブ/点滴ノズル -> プランター
```

注意:

- 手動バルブは必須です
- 流量調整バルブも入れます
- 実験外時間、外出時、就寝時は手動バルブを閉じます
- 長時間不在時は 12V 電源も落とします
- 水やりが止まらない場合は、まず手動バルブを閉め、次に 12V 電源を切ります

## テスト手順

### Arduino単体 dry-run テスト

1. `DRY_RUN_MODE=true` を確認する
2. Arduino に書き込む
3. シリアルモニタを `115200bps` で開く
4. 起動時 JSON で `valve_open=false` を確認する
5. `status` を実行する
6. `read` を実行する
7. `water 1000` で LED が 1 秒点灯することを確認する
8. `water 100000` で `MAX_SINGLE_WATER_MS` に切り詰められることを確認する
9. センサーを湿らせて `water 1000` が `soil_too_wet` で拒否されることを確認する
10. `close` で LED / バルブ制御が OFF になることを確認する
11. 不正コマンドで `error` JSON が返り、バルブが閉じることを確認する

### 手動で値を確認する方法

`arduino-cli` ではボード確認とモニタ起動ができます。

```bash
/home/kansei/bin/arduino-cli board list
/home/kansei/bin/arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

モニタを開いたら、次のように 1 行ずつ入力します。

```text
status
read
water 1000
close
```

WSL で簡易に 1 コマンドだけ送りたい場合は、別ターミナルから次でも確認できます。

```bash
stty -F /dev/ttyACM0 115200 raw -echo -echoe -echok -echoctl -echoke -icanon min 0 time 20
exec 3<> /dev/ttyACM0
printf 'read\n' >&3
IFS= read -r -t 4 line <&3 && printf '%s\n' "$line"
exec 3>&-
exec 3<&-
```

### MOSFETモジュール接続後テスト

1. まだ水を接続しない
2. `DRY_RUN_MODE=false` に変更する
3. バルブの代わりに LED やテスターで MOSFET 出力の ON/OFF を確認する
4. 短い `water 500` で出力が ON/OFF することを確認する
5. 電磁バルブだけを接続し、水なしでカチッと動作するか確認する
6. その後、流量調整バルブを絞った状態で水テストする

## JSONレスポンス例

### `read`

```json
{
  "status": "ok",
  "command": "read",
  "soil_moisture_raw": 612,
  "soil_moisture_percent": 42.5,
  "is_wet": false
}
```

### `status`

```json
{
  "status": "ok",
  "command": "status",
  "uptime_ms": 123456,
  "valve_open": false,
  "dry_run": true,
  "daily_watered_ms": 0,
  "max_single_water_ms": 5000,
  "max_daily_water_ms": 30000,
  "wet_reject_percent": 75.0,
  "soil_moisture_raw": 612,
  "soil_moisture_percent": 42.5,
  "is_wet": false
}
```

### `close`

```json
{
  "status": "ok",
  "command": "close",
  "valve_open": false,
  "message": "valve_closed"
}
```

### `water` 成功

```json
{
  "status": "ok",
  "command": "water",
  "moisture_before_percent": 41.2,
  "moisture_after_percent": 54.8,
  "requested_duration_ms": 1000,
  "actual_duration_ms": 1000,
  "applied_limit": false,
  "dry_run": true,
  "message": "watered"
}
```

### `water` 上限切り詰め

```json
{
  "status": "ok",
  "command": "water",
  "moisture_before_percent": 41.2,
  "moisture_after_percent": 43.0,
  "requested_duration_ms": 10000,
  "actual_duration_ms": 5000,
  "applied_limit": true,
  "dry_run": true,
  "message": "watered_with_limit"
}
```

### `water` wet 拒否

```json
{
  "status": "rejected_by_safety",
  "command": "water",
  "reason": "soil_too_wet",
  "moisture_before_percent": 82.1,
  "requested_duration_ms": 3000,
  "actual_duration_ms": 0,
  "dry_run": true,
  "message": "rejected"
}
```

### `water` 日次上限拒否

```json
{
  "status": "rejected_by_safety",
  "command": "water",
  "reason": "daily_limit_exceeded",
  "requested_duration_ms": 3000,
  "actual_duration_ms": 0,
  "daily_watered_ms": 30000,
  "max_daily_water_ms": 30000,
  "dry_run": true,
  "message": "rejected"
}
```

### 不正コマンド

```json
{
  "status": "error",
  "command": "unknown",
  "reason": "unknown_command",
  "valve_open": false,
  "message": "rejected"
}
```

## 注意点

- 日次上限は RTC 未使用のため「起動後 24 時間窓」で管理しています
- `water` 実行中も最後に必ず `closeValve()` を通ります
- `moisture_after` はバルブを閉じたあと `AFTER_WATER_READ_DELAY_MS` 待ってから読みます
- この待機は Arduino 単体レスポンス確認用です。本格的な効果測定は将来 Raspberry Pi 側で 5 分間隔に行います
- 将来、Raspberry Pi は定期的に `read` を実行して土壌水分を記録します
- 朝・夕方の判断タイミングでのみ、AI エージェント判断に従って `water <duration_ms>` を送る想定です
- 実バルブ接続前は `DRY_RUN_MODE=true` のまま机上試験してください
- `SOIL_SENSOR_DRY_RAW=472` と `SOIL_SENSOR_WET_RAW=256` は現時点の机上確認用の暫定値です

## WSL2 + arduino-cli でのビルド/書き込み

WSL 上の Codex からコンパイル・書き込みするための手順です。

### 初回セットアップ

```bash
# arduino-cli と UNO R4 ボード定義を入れる
./tools/setup_wsl_arduino.sh
```

Windows 側（管理者 PowerShell）で USB を WSL に渡す準備:

```powershell
winget install --id dorssel.usbipd-win
usbipd list
usbipd bind --busid <BUSID>
```

### 日常の使い方

```bash
cd edge/arduino/valve_controller

make compile
make attach-usb
make upload
make monitor
make board-list
```

FQBN は `arduino:renesas_uno:unor4wifi` です。
