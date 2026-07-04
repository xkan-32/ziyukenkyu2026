# Raspberry Pi 観測基盤 — リポジトリ実装 + ドライランテスト

komatsuna-ai-agent リポジトリの `edge/raspberry-pi/` に、**観測基盤の初期実装**を行ってください。

このプロンプトのスコープは **リポジトリ上のコード作成と、ハードウェア不要のドライランテスト** です。Raspberry Pi へのデプロイ・実機 SSH 作業は **このプロンプトでは行わない** でください。

---

## 目的

Arduino から土壌水分を読み取り、（可能なら）カメラ画像を取得し、ローカル JSONL に保存し、GCP 送信を試みる（未設定時はスタブ/スキップ）**通常観測フロー**を Raspberry Pi 側に実装する。

---

## 必ず最初に読むファイル

実装前に以下を読み、設計に従うこと。

- `README.md`
- `CODE.md`
- `docs/03_system_design.md`
- `docs/04_detail_design.md`
- `docs/05_data_design.md`
- `docs/07_safety.md`
- `docs/progress/current_implementation_status.md`
- `edge/arduino/valve_controller/README.md`（JSON レスポンス契約）
- `edge/arduino/valve_controller/valve_controller.ino`（実際のフィールド名を確認）

---

## スコープ（やること）

1. Arduino USB シリアル通信（`read` / `status` / `close` のみ）
2. レスポンス JSON のパースと型付き dataclass / Pydantic モデル
3. ローカル JSONL 保存（観測・土壌水分・再送キュー）
4. カメラ撮影・リサイズ（未接続時はスキップ可能）
5. 通常観測スケジューラ（1 回実行 + 手動 CLI）
6. GCP 同期の骨格（資格情報未設定時は no-op / ローカルキューへ退避）
7. **ドライランモード**（シリアル/カメラ/GCP をモックまたはスキップ）
8. **pytest によるユニットテスト**
9. **CLI スクリプト**（`scripts/test_serial.sh`, `scripts/test_camera.sh` の実装）
10. `config.py` / `.env.example` の拡張

---

## スコープ外（やらないこと）

- `water` コマンドの送信（コードに経路を作らない。将来用の stub も不要）
- AI 判断（`POST /judge`）の呼び出し
- 水やり後高頻度測定（`post_watering_scheduler.py` は TODO コメントのみ残す）
- Raspberry Pi への SSH デプロイ
- Arduino ファームウェアの変更
- GCP インフラ（Terraform）のデプロイ
- `human_task` / `line_webhook` 関連

---

## 安全制約（必須）

- `ALLOW_WATER_COMMAND_FROM_PI=false` を **既定値** とする（`config.py` + `.env.example`）
- 観測フローから `water` へ到達するコードを書かない
- 乾燥値だけで自動水やりしない
- Arduino 側 `DRY_RUN_MODE` は変更しない

---

## 作成・更新するファイル

### 新規作成

```
edge/raspberry-pi/
  app/
    models/
      __init__.py
      arduino_response.py      # read/status/close/error レスポンスモデル
      observation.py           # docs/05_data_design.md の observations 契約
      local_queue.py           # 再送キュー用レコード
    storage/
      __init__.py
      local_jsonl_store.py     # JSONL 追記・読み取り
      local_queue_store.py     # 再送キュー（JSONL ベースで可）
    arduino/
      mock_serial.py           # ドライラン用モック（固定 JSON 応答）
    camera/
      mock_capture.py          # テスト用ダミー画像生成（Pillow）
  tests/
    __init__.py
    conftest.py
    test_arduino_commands.py
    test_serial_client.py
    test_local_jsonl_store.py
    test_observation_scheduler.py
    test_observation_dry_run.py
  .env.example                 # edge/raspberry-pi 用（またはルート .env.example を更新）
```

### 既存ファイルを実装で置き換え

- `edge/raspberry-pi/app/config.py`
- `edge/raspberry-pi/app/arduino/commands.py`
- `edge/raspberry-pi/app/arduino/serial_client.py`
- `edge/raspberry-pi/app/camera/capture.py`
- `edge/raspberry-pi/app/camera/image_resize.py`
- `edge/raspberry-pi/app/scheduler/observation_scheduler.py`
- `edge/raspberry-pi/app/gcp/firestore_sync.py`（スタブ: 資格情報なしなら False を返しキューへ）
- `edge/raspberry-pi/app/gcp/storage_upload.py`（同上）
- `edge/raspberry-pi/app/gcp/agent_api_client.py`（未使用 stub のみ、judge は呼ばない）
- `edge/raspberry-pi/app/main.py`
- `edge/raspberry-pi/scripts/test_serial.sh`
- `edge/raspberry-pi/scripts/test_camera.sh`
- `edge/raspberry-pi/scripts/install.sh`（最小: venv + pip install + データディレクトリ作成）
- `edge/raspberry-pi/requirements.txt`（pytest 追加）
- `edge/raspberry-pi/systemd/komatsuna-agent.service`（パスを実装に合わせて更新）

---

## 設定（config.py / .env.example）

以下の環境変数を定義すること。

| 変数 | 既定値 | 説明 |
|------|--------|------|
| `ARDUINO_SERIAL_PORT` | `/dev/ttyACM0` | シリアルポート |
| `ARDUINO_BAUD_RATE` | `115200` | ボーレート |
| `ALLOW_WATER_COMMAND_FROM_PI` | `false` | **必ず false 既定** |
| `DRY_RUN_MODE` | `true` | Pi 側ドライラン（モックシリアル/モックカメラ使用） |
| `EXPERIMENT_ROUND_ID` | `round_1` | `docs/05_data_design.md` に合わせる |
| `PLANTER_PROFILE_ID` | `ai_planter_a` | 同上 |
| `LOCAL_DATA_DIR` | `./data/local` | JSONL・画像・キューのルート |
| `OBSERVATION_INTERVAL_MINUTES` | `60` | 通常観測間隔（CLI 1 回実行では未使用可） |
| `GCP_PROJECT_ID` | 空 | 空なら GCP 同期スキップ |
| `GCS_BUCKET_NAME` | 空 | 空なら GCS アップロードスキップ |
| `AGENT_API_URL` | 空 | 初期フェーズでは未使用 |
| `LOG_LEVEL` | `INFO` | ログレベル |

**削除または非推奨:** `CULTIVATION_GROUP` は使わず、`EXPERIMENT_ROUND_ID` / `PLANTER_PROFILE_ID` に統一する。

---

## Arduino シリアル契約

### 送るコマンド（平文、末尾 `\n`）

```
read
status
close
```

### 受け取る JSON（1 行）— 実装のフィールド名に合わせる

**read 成功例:**

```json
{"status":"ok","command":"read","soil_moisture_raw":472,"soil_moisture_percent":0.0,"is_wet":false}
```

**status 成功例:**

```json
{"status":"ok","command":"status","uptime_ms":17911,"valve_open":false,"dry_run":true,"daily_watered_ms":0,"max_single_water_ms":5000,"max_daily_water_ms":30000,"wet_reject_percent":75.0,"soil_moisture_raw":472,"soil_moisture_percent":0.0,"is_wet":false}
```

**close 成功例:**

```json
{"status":"ok","command":"close","valve_open":false,"message":"valve_closed"}
```

**error 例:**

```json
{"status":"error","command":"unknown","reason":"unknown_command","valve_open":false,"message":"rejected"}
```

### serial_client.py の要件

- `pyserial` 使用
- タイムアウト付き（例: 読み取り 3 秒、コマンド応答待ち 5 秒）
- 1 行 JSON を読み取り、`json.loads` でパース
- パース失敗・タイムアウト時は例外を投げ、観測は `device_error` として記録
- `DRY_RUN_MODE=true` のときは `mock_serial.py` を使い、実ポートを開かない
- コンテキストマネージャまたは `open()` / `close()` でポート管理

### commands.py の要件

- `read_moisture() -> ReadResponse`
- `get_status() -> StatusResponse`
- `close_valve() -> CloseResponse`
- **`send_water_command` は実装しない**

---

## 観測データ契約（observation.py）

`docs/05_data_design.md` の `observations` に合わせる。最低限:

```python
{
  "id": "obs_YYYYMMDD_HHMMSS_<planter_profile_id>",
  "experiment_round_id": "...",
  "planter_profile_id": "...",
  "observed_at": "ISO8601+09:00",
  "observation_type": "scheduled",  # 初期は scheduled 固定で可
  "soil_moisture_raw": int | null,
  "soil_moisture_percent": float | null,
  "image_local_path": str | null,       # GCS 未設定時はローカルパス
  "thumbnail_local_path": str | null,
  "image_gcs_path": str | null,
  "thumbnail_gcs_path": str | null,
  "weather_summary": str | null,        # 初期は null で可
  "source": "raspberry_pi",
  "device_status": "ok" | "partial" | "device_error",
  "arduino_status_response": dict | null  # status コマンド結果（デバッグ用、任意）
}
```

---

## ローカル JSONL 保存（local_jsonl_store.py）

- `{LOCAL_DATA_DIR}/observations.jsonl` — 観測 1 行 1 JSON
- `{LOCAL_DATA_DIR}/soil_moisture_readings.jsonl` — 土壌水分のみ（`measurement_phase=normal_periodic`）
- `{LOCAL_DATA_DIR}/local_queue.jsonl` — GCP 送信待ち

要件:

- 追記は atomic に近い実装（追記のみ、上書きしない）
- ディレクトリが無ければ作成
- `append_observation()`, `append_soil_reading()`, `enqueue_for_sync()` 等の API

---

## 通常観測シーケンス（observation_scheduler.py）

`run_observation_cycle()` を実装:

1. `close` を送ってバルブ閉を確認（失敗しても観測は続行可、ログに warn）
2. `read` で土壌水分取得
3. `status` でデバイス状態取得（任意だが推奨）
4. カメラ利用可能なら撮影 + リサイズ（`DRY_RUN_MODE` またはカメラ未接続なら mock / skip）
5. 観測レコードを組み立て
6. **必ず** ローカル JSONL へ保存（GCP より先）
7. GCP 資格情報があれば Firestore / GCS へ送信、失敗時は `local_queue` へ
8. **`water` は呼ばない**

---

## カメラ（capture.py / image_resize.py）

- Raspberry Pi では `libcamera-still` または `picamera2` を試し、無ければ Pillow でダミー画像
- `DRY_RUN_MODE=true` または `CAMERA_ENABLED=false` なら mock
- 原本: `{LOCAL_DATA_DIR}/images/YYYYMMDD_HHMMSS.jpg`
- サムネ: `{LOCAL_DATA_DIR}/images/YYYYMMDD_HHMMSS_small.jpg`（長辺 640px 程度）

---

## GCP 同期（スタブ）

- `GCP_PROJECT_ID` が空 → `sync_observation()` は `False` を返し、キューへ enqueue
- 実装は try/except で囲み、例外を握りつぶさずログ + キュー退避
- Firestore / GCS の本格 SDK 呼び出しは TODO コメント + 最小 stub で可（資格情報あり環境向けの骨格だけ）

---

## main.py

CLI 引数をサポート:

```bash
python -m app.main --dry-run once          # 観測 1 サイクル（DRY_RUN_MODE 強制）
python -m app.main once                    # 観測 1 サイクル
python -m app.main --help
```

`--dry-run` 指定時は環境変数に関わらずモック使用。

---

## ドライランテスト（必須）

### pytest

リポジトリルートまたは `edge/raspberry-pi/` から実行可能にする。

```bash
cd edge/raspberry-pi
python -m pytest tests/ -v
```

テスト内容（最低限）:

| テスト | 内容 |
|--------|------|
| `test_arduino_commands` | モック JSON から dataclass へパース |
| `test_serial_client` | モックシリアルで read/status/close |
| `test_local_jsonl_store` | tmp_path に追記・読み取り |
| `test_observation_scheduler` | ドライラン 1 サイクルで JSONL 1 行追加 |
| `test_observation_dry_run` | `ALLOW_WATER_COMMAND_FROM_PI` が false のまま、`water` 文字列がコードに無いことを間接確認 |

### シェルスクリプト

**scripts/test_serial.sh** — ドライラン:

```bash
cd edge/raspberry-pi
DRY_RUN_MODE=true python -m app.main --dry-run once
# 終了コード 0、observations.jsonl に 1 行以上
```

**scripts/test_camera.sh** — ドライラン:

```bash
cd edge/raspberry-pi
DRY_RUN_MODE=true python -c "from app.camera.capture import capture_image; print(capture_image())"
# パスが返る or skip メッセージ
```

### 完了時に実行して結果を報告すること

```bash
cd edge/raspberry-pi
pip install -r requirements.txt
python -m pytest tests/ -v
DRY_RUN_MODE=true python -m app.main --dry-run once
ls -la data/local/   # または LOCAL_DATA_DIR
tail -n 1 data/local/observations.jsonl
bash scripts/test_serial.sh
```

---

## コーディング規約

- 既存の `app/` パッケージ構成に合わせる
- 型ヒントを付ける
- ログは `logging` モジュール（print 禁止）
- 過剰な抽象化を避ける
- コメントは非自明な業務ロジックのみ
- `docs/05_data_design.md` のフィールド名を優先（`cultivation_group` は使わない）

---

## 受け入れ条件

- [ ] `read` / `status` / `close` クライアントがモックで動作
- [ ] 観測 1 サイクルで `observations.jsonl` に 1 行追記される
- [ ] `ALLOW_WATER_COMMAND_FROM_PI=false` が config 既定
- [ ] `water` 送信コードが存在しない
- [ ] `pytest` がすべて pass
- [ ] `scripts/test_serial.sh` が exit 0
- [ ] GCP 未設定でも例外で落ちず、キューまたはスキップで完走
- [ ] Arduino ファームウェアに変更なし

---

## 完了報告フォーマット

実装後、以下を Markdown で報告すること。

1. 作成・変更したファイル一覧
2. `pytest` 結果（pass/fail 数）
3. `--dry-run once` 実行ログ要約
4. `observations.jsonl` のサンプル 1 行
5. 設計書との差分があれば明記
6. 次ステップ（Pi 実機デプロイ）で必要な作業リスト

---

## 禁止事項

- Raspberry Pi への SSH デプロイ
- `water` コマンド送信の実装
- Arduino ファームウェア変更
- 秘密情報のコミット
- 未テストのまま「完了」と報告しない
