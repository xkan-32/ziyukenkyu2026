# 現在の実装状況

最終更新: 2026-07-05
対象リポジトリ: komatsuna-ai-agent

## 1. 全体方針の再確認

- 事実
  - AI 側の小松菜栽培ログを保存するシステム、という方針は [README.md](/home/kansei/AI/ziyukenkyu2026/README.md) と [CODE.md](/home/kansei/AI/ziyukenkyu2026/CODE.md) に明記されている
  - 人間側の判断・作業・写真・収穫結果はシステムに保存しない方針が明記されている
  - Raspberry Pi は観測・通信・ローカルスケジュール担当、Arduino は安全制御付き実行装置、Cloud Run / Gemini は判断担当、という責務分離が設計書にある
  - 定期観測と AI 判断は分離し、乾燥しているだけでは自動水やりしない方針が設計書にある
  - Arduino は `water <duration_ms>` の安全実行可否だけを判定し、水やり要否は判断しない方針が Arduino README と実装に一致している
- 判断
  - ドキュメント上の設計思想は一貫している
  - 現時点で実装が最も進んでいるのは Arduino
  - Raspberry Pi / GCP / AI は多くが骨格またはプレースホルダー段階
  - 次フェーズは Raspberry Pi 観測基盤の初期実装であり、自動散水本番化はまだ次段階

## 2. 現在の実装範囲

- 実装済み
  - Arduino `edge/arduino/valve_controller/` の安全制御ファームウェア
  - Arduino 実機の dry-run と MOSFET 経由の電磁バルブ単体動作確認
  - Raspberry Pi 側の観測基盤初期実装、実機デプロイ、systemd timer 有効化
  - Cloud Run `agent-api` の FastAPI エントリポイントと `GET /health`
  - Terraform の dev/prod 雛形
- 一部のみ存在
  - `agent-api` の `/judge`、`/watering/effect/analyze`、改善・日次サマリー・エクスポートはルーター名とファイルはあるが実装未完了
- 未実装
  - AI 判断に基づく自動水やり実行
  - 水やり後のローカル高頻度測定の実装
  - Firestore / GCS / Vertex AI 実接続
  - Terraform モジュール呼び出し

## 3. Arduino 実装状況

### 3.1 実装済み機能

- 実装ディレクトリ: `edge/arduino/valve_controller/`
- 主要ファイル
  - [README.md](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/README.md)
  - [config.h](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/config.h)
  - [valve_controller.ino](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/valve_controller.ino)
  - [sensor.h](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/sensor.h)
  - [valve.h](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/valve.h)
  - [safety.h](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/safety.h)
  - [serial_protocol.h](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/serial_protocol.h)
  - [Makefile](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/Makefile)
- 実装済みコマンド
  - `read`
  - `status`
  - `close`
  - `water <duration_ms>`
- `water` の安全判定
  - wet 拒否: あり
  - 単回最大開放時間: あり
  - 24 時間窓の累積上限: あり
  - 不正コマンド拒否: あり
  - 起動時・異常時・不正時のバルブ閉止: あり
- その他
  - 土壌水分 raw -> percent 変換: あり
  - センサー読み取り平均化: あり
  - dry-run mode: あり
  - MOSFET モジュール制御: あり
  - JSON レスポンス: すべて 1 行 JSON

### 3.2 設定値

| 項目 | 現在値 |
| -- | -- |
| `SERIAL_BAUD` | `115200` |
| `VALVE_PIN` | `2` |
| `SOIL_MOISTURE_PIN` | `A0` |
| `TEST_LED_PIN` | `LED_BUILTIN` |
| `VALVE_ACTIVE_HIGH` | `true` |
| `DRY_RUN_MODE` | `true`（repo 既定値） |
| `SOIL_SENSOR_DRY_RAW` | `472` |
| `SOIL_SENSOR_WET_RAW` | `256` |
| `WET_REJECT_PERCENT` | `75.0` |
| `SENSOR_READ_SAMPLES` | `10` |
| `SENSOR_READ_INTERVAL_MS` | `10` |
| `AFTER_WATER_READ_DELAY_MS` | `1000` |
| `MAX_SINGLE_WATER_MS` | `5000` |
| `MAX_DAILY_WATER_MS` | `30000` |

### 3.3 実機確認済み項目

- dry-run 書き込み確認: 済み
- dry-run `status`: 確認済み
- dry-run `read`: 確認済み
- dry-run `water 500`: 確認済み
- dry-run `water 100000`: `actual_duration_ms=5000` に切り詰め確認済み
- `DRY_RUN_MODE=false` での実機モード確認: 済み
- Raspberry Pi からの `status/read/close/water 300/water 100000` 確認: 済み
- 湿潤状態での `soil_too_wet` 拒否確認: 済み
- 乾燥・湿潤でのセンサー値変化確認: 済み
- MOSFET モジュール経由の電磁バルブ動作確認: 済み
- 電磁バルブの「カチッ」確認: ユーザー確認済み
- `close` 確認: 毎回 `valve_open=false`
- `water 100000` の上限切り詰め確認: 済み
- 不正コマンド拒否確認: `abc` で確認済み
- `water` 単体の扱い: `unknown_command`
- `water abc` の扱い: `invalid_duration_ms`
- wet 拒否確認
  - 元の `WET_REJECT_PERCENT=75.0` で、湿潤時 `soil_moisture_percent=100.0` により `soil_too_wet` を確認
- 水道接続: 未実施
- 流量測定: 未実施

代表レスポンス:

```json
{"status":"ok","command":"status","uptime_ms":106382,"valve_open":false,"dry_run":false,"daily_watered_ms":0,"max_single_water_ms":5000,"max_daily_water_ms":30000,"wet_reject_percent":75.0,"soil_moisture_raw":464,"soil_moisture_percent":3.7,"is_wet":false}
{"status":"ok","command":"water","moisture_before_percent":3.2,"moisture_after_percent":3.2,"requested_duration_ms":100000,"actual_duration_ms":5000,"applied_limit":true,"dry_run":false,"message":"watered_with_limit"}
{"status":"rejected_by_safety","command":"water","reason":"soil_too_wet","moisture_before_percent":100.0,"requested_duration_ms":300,"actual_duration_ms":0,"daily_watered_ms":300,"dry_run":false,"message":"rejected"}
```

### 3.4 未確認・未実施項目

- 水道・給水接続
- 流量調整バルブを含む通水試験
- 流量測定
- MOSFET モジュールの発熱確認
- 12V 電源の異常有無確認
- `daily_limit_exceeded` の実機確認
- USB 抜去、電源断、Pi 停止時の安全試験

### 3.5 安全設計との対応

- 一致している点
  - 起動時にバルブを閉じる
  - `water` 実行前に wet 判定を行う
  - 単回上限と 24 時間窓の累積上限がある
  - 不正コマンドでバルブを閉じる
  - dry-run で実バルブを開かず机上試験できる
- 要確認
  - wet 閾値の本番値は未校正
  - 日次上限は RTC なしのため「起動後 24 時間窓」

## 4. Raspberry Pi 実装状況

### 4.1 実装済み機能

- 実装ディレクトリ
  - `app/`
  - `app/arduino/`
  - `app/camera/`
  - `app/gcp/`
  - `app/models/`
  - `app/scheduler/`
  - `app/storage/`
  - `scripts/`
  - `systemd/`
- 依存関係ファイル
  - `pyserial`
  - `google-cloud-firestore`
  - `google-cloud-storage`
  - `requests`
  - `Pillow`
  - `pytest`
- 設定ファイルあり
  - `ARDUINO_SERIAL_PORT=/dev/ttyACM0`
  - `ARDUINO_BAUD_RATE=115200`
  - `ALLOW_WATER_COMMAND_FROM_PI=false`
  - `DRY_RUN_MODE=true`（Pi `.env` では実機観測時に `false` を使用）
- systemd service/timer を Pi 実機へ配置して有効化済み

### 4.2 実装済み機能

- `read/status/close` の Python クライアント
  - `app/arduino/serial_client.py`
  - `app/arduino/commands.py`
- ローカル JSONL 保存
  - `app/storage/local_jsonl_store.py`
  - `app/storage/local_queue_store.py`
- 定期スケジューラ本体
  - `app/scheduler/observation_scheduler.py`
  - `app/scheduler/post_watering_scheduler.py` は TODO コメントのみ
- カメラ撮影とリサイズ
  - `app/camera/capture.py`
  - `app/camera/image_resize.py`
  - `app/camera/mock_capture.py`
- GCP 同期の骨格
  - `app/gcp/firestore_sync.py`
  - `app/gcp/storage_upload.py`
  - `app/gcp/agent_api_client.py`
- `water` 自動実行は未実装のまま維持
  - `app/main.py` は観測 1 サイクル専用 CLI
- `ALLOW_WATER_COMMAND_FROM_PI=false` を既定値として実装

### 4.3 現時点の位置づけ

- Raspberry Pi 側は「観測基盤の初期実装」まで完了
- dry-run での 1 サイクル観測、JSONL 保存、画像生成、ローカルキュー退避を確認済み
- Pi 実機で `python -m app.main once`、Arduino 通信、JSONL 保存、systemd timer を確認済み
- Pi カメラは `rpicam-still` 経由で実撮影を確認済み
- GCP 実接続は次段階

## 5. GCP / Cloud Run / Firestore / GCS 実装状況

- Cloud Run
  - `services/agent-api/app/main.py` で FastAPI エントリポイントあり
  - `GET /health` は実装済み
  - `/judge`: ルーターのみ、未実装
  - `/watering/effect/analyze`: ルーターのみ、未実装
  - `/improve`: ファイルはあるが今回未確認、進捗上は未完成扱いが妥当
  - `/daily-summary`: ファイルはあるが今回未確認、進捗上は未完成扱いが妥当
  - `/export/research-data`: ファイルはあるが今回未確認、進捗上は未完成扱いが妥当
- Firestore
  - データ設計書は詳細にある
  - クライアント実装は TODO
- GCS
  - 設計書はある
  - 実装は TODO
- Vertex AI Gemini
  - 設定項目あり
  - クライアント実装は TODO
- 日次サマリー
  - 設計あり
  - 実装未完了
- エクスポート
  - 設計あり
  - 実装未完了

## 6. AIエージェント実装状況

- 実装済み
  - プロンプト設計文書あり
  - `services/agent-api/app/prompts/` に `judge.md`、`watering_effect.md`、`improvement.md` 等あり
  - `agent-api` のスキーマファイル群あり
- 未実装
  - `judge_cultivation.py` は TODO
  - `analyze_watering_effect.py` は TODO
  - Gemini クライアントは TODO
- 要確認
  - `line_webhook`、`human_task`、`verify_human_task` など、設計書の中心スコープより広い名前のファイルが存在する
  - ただし現状はいずれも未使用で、初期スコープでは使わない旨の注記がコード内にある

## 7. データ保存・ログ設計との対応

- 設計済み
  - `observations`
  - `ai_decisions`
  - `watering_events`
  - `soil_moisture_readings`
  - `watering_effect_analyses`
- 実装済み
  - Arduino の JSON 契約は存在
  - 実機テストログは [TEST_LOG.md](/home/kansei/AI/ziyukenkyu2026/edge/arduino/valve_controller/TEST_LOG.md) に記録済み
- 実装済み
  - Raspberry Pi からのローカル JSONL 蓄積
- Firestore への保存
- GCS への画像保存
- AI 判断結果の永続化
- 水やり後効果測定の継続保存

## 8. 現在の実機テスト結果

- 事実
  - Arduino コンパイル成功
  - Arduino 書き込み成功
  - dry-run `status/read/water 500/close/water 100000` を確認
  - 実機モードで `water 300` と `water 100000`、`close` を確認
  - 電磁バルブは `water` 実行時だけ「カチッ」と動作
  - `water 100000` は `5000ms` へ切り詰め
  - 湿潤状態では `soil_too_wet` により `water 300` を拒否
  - センサーは乾燥時 `1.4-3.7%`、湿潤時 `100.0%` を記録
  - Pi 実機で `python -m app.main once` が成功し、`observations.jsonl` と `soil_moisture_readings.jsonl` に追記
  - Pi カメラは `rpicam-still` で実画像を保存
  - `komatsuna-agent.timer` は有効化済み
- 未テスト
  - 水道接続後の通水試験
  - 流量測定
  - 長時間運転時の発熱
  - 異常停止系の安全試験

## 9. 設計思想との相違チェック

| 観点 | 設計方針 | 現在の実装 | 判定 | メモ |
| -- | ---- | ----- | -- | -- |
| Arduinoが水やり判断をしない | 実行可否だけを判定 | `water` の安全判定のみ実装 | OK | 自動判断ロジックはない |
| 乾燥値だけで自動水やりしない | 定期観測と判断を分離 | Arduino 単体では自動通水なし | OK | Pi 側自動化は未実装 |
| wet時はArduinoが拒否する | wet 閾値以上で拒否 | 実装あり、実機で `soil_too_wet` を確認 | OK | 本番閾値は未校正 |
| 単回最大開放時間がある | 上限強制 | `5000ms` 上限あり | OK | 実機確認済み |
| 1日累積上限がある | 日次上限強制 | `30000ms` 実装あり | OK | 実機未確認 |
| 起動時・異常時に閉じる | 閉側へ倒す | boot で `closeValve()` 実装 | OK | USB 抜去等は未テスト |
| Raspberry Piはまず観測係である | 観測・通信・スケジュール担当 | 観測基盤を実装し実機確認済み | OK | 自動水やり経路は未実装 |
| AI判断は朝・夕方のみの想定 | decision window のみ | ドキュメントでは明記、実装未着手 | 未実装 | 実装時に要維持 |
| 人間側データを保存しない | システム外管理 | ドキュメント上は維持 | OK | human_task 系は将来用として未使用に固定する |
| 水道接続前に安全確認する | 先に dry-run / 電気試験 | 実機手順どおり実施 | OK | 水道接続は未実施 |
| GCP/AIは未実装なら未実装として扱う | 過大主張しない | 現状は雛形中心 | OK | `/health` 以外は未完成 |
| Raspberry Pi 初期実装は観測基盤に限定する | 観測・通信・ローカル保存を先行 | 実装・実機確認済み | OK | `water` 自動実行は初期スコープ外 |

## 10. 現時点のリスク・注意点

- 土壌水分センサー校正値は暫定であり、実土壌で再校正が必要
- 水道接続前に流量調整バルブと手動バルブが必要
- 流量測定は未実施
- Raspberry Pi の定期観測 timer は有効化済み
- AI 判断前は自動水やり判断は未実装
- 12V 系と Arduino 5V 系の混同に注意
- 緊急時は手動バルブと 12V 電源遮断が優先
- repo 既定値の `DRY_RUN_MODE=true` と、実機試験時の書き込み設定 `dry_run=false` を混同しないよう注意
- `ALLOW_WATER_COMMAND_FROM_PI=false` は実装済みで、Pi `.env` でも維持している
- `tools/attach_arduino_usb.sh` は WSL2 用の補助スクリプト修正が入っている

## 11. 次に実装すべきこと

1. Raspberry Pi から Arduino への USB シリアル通信
   - 現状: ファイルはあるが未実装
2. `read/status/close` の Python クライアント
   - 現状: 未実装
3. ローカル JSONL 保存
   - 現状: 未実装、対象ファイルも未作成
4. カメラ撮影・リサイズ
   - 現状: TODO
5. 定期観測スケジューラ
   - 現状: TODO
6. GCP 送信失敗時のローカル退避と再送キュー
   - 現状: 設計のみ
7. `ALLOW_WATER_COMMAND_FROM_PI=false` を既定とする安全フラグ追加
   - 現状: 未実装
8. 流量測定
   - 現状: 未実施
9. GCP 最小構成
   - 現状: FastAPI `/health` と Terraform 雛形のみ
10. AI 判断 API
   - 現状: ルーター雛形のみ
11. AI 判断に基づく水やり実行の解禁条件整理
   - 現状: 校正・安全試験が未完了のため着手しても本番無効の前提
12. 水やり後の効果測定
   - 現状: 設計のみ、スケジューラ TODO
