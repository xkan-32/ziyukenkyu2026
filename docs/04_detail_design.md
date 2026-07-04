# Raspberry Pi処理詳細

## 推奨モジュール分割

- `camera/`
  - 撮影、リサイズ、ファイル名採番
- `arduino/`
  - コマンド定義、シリアル通信、レスポンス検証
- `gcp/`
  - Cloud Storage アップロード、Firestore 同期、agent-api 呼び出し
- `scheduler/observation_scheduler.py`
  - 通常時の観測
- `scheduler/post_watering_scheduler.py`
  - 水やり後 5 分間隔測定

## Raspberry Pi 初期実装フェーズ

初期実装フェーズでは Raspberry Pi を観測基盤として先に完成させる。対象は次に限定する。

- Arduino USB シリアル通信
- `read` / `status` / `close` の Python クライアント
- ローカル JSONL 保存
- カメラ撮影・リサイズ
- 通常観測スケジューラ
- GCP 送信失敗時のローカル退避

初期フェーズでは AI 判断に基づく `water` 自動実行、水道接続した本番散水、水やり後の本番効果測定運用は解禁しない。

## 通常観測シーケンス

1. Raspberry Pi が現在時刻を確認する
2. カメラ撮影が必要な観測タイミングなら画像を撮影する
3. Arduino に `read` を送り、土壌水分 raw / percent を取得する
4. 必要なら天気を取得する
5. 送信前にローカル JSONL へ保存する
6. GCP 送信に成功したら Firestore / GCS へ反映する
7. 通常観測では水やりを実行しない

## AI判断シーケンス

1. 朝・夕方の decision window でのみ実行する
2. 最新の観測、直近履歴、画像、天気を agent-api の `POST /judge` に送る
3. AI が `water`、`observe_only`、`manual_review` などを JSON で返す
4. `ai_decisions` に保存する
5. `action=water` の場合のみ、Raspberry Pi が mL を duration_ms に変換する
6. `ALLOW_WATER_COMMAND_FROM_PI=false` の間はここで停止し、提案だけを保存する
7. 明示設定で許可された場合のみ Raspberry Pi が Arduino に `water <duration_ms>` を送る
8. Arduino が wet 判定、単回上限、日次上限で安全判定する
9. 実行結果または拒否結果を `watering_events` に保存する
10. 成功時のみ、水やり後 5 分間隔の効果測定を開始する

## 水やりシーケンス

1. `ai_decisions` の提案 mL を受け取る
2. ローカル校正値で mL -> ms に換算する
3. Raspberry Pi 側でも最大許容時間を上限として適用する
4. `ALLOW_WATER_COMMAND_FROM_PI=false` なら送信せず、提案保存で終了する
5. `ALLOW_WATER_COMMAND_FROM_PI=true` のときだけ `water <duration_ms>` を Arduino に送る
6. レスポンスを `watering_events` に保存する
7. `status=success` のときだけ高頻度測定を開始する

## 定期土壌水分測定シーケンス

1. Raspberry Pi が一定間隔で Arduino に `read` を送る
2. 土壌水分 raw / percent を取得する
3. データ蓄積目的で保存する
4. 乾燥していても、このシーケンス単独では水やりしない

## オフライン時の扱い

- GCP 送信失敗時はローカルキューへ書く
- すべての送信対象は送信前にローカル JSONL へ追記する
- キュー対象
  - observation
  - watering_event
  - soil_moisture_reading
  - weather_log
- 初期スコープ外
  - human_task
  - verify_human_task
  - line_webhook
- 再送時は元の `occurred_at` を保持し、送信時刻を別フィールドに入れる

# Arduino処理詳細

## コマンド案

- `read`
  - 現在の土壌水分値を返す
- `water <duration_ms>`
  - 安全判定の上で通水する
- `status`
  - 起動時間、当日累積開放時間、閾値などを返す
- `close`
  - バルブを強制閉止する

初期実装では 1 行 1 コマンドの平文入力に対して、1 行 JSON を返す。
`water` は `duration_ms` の形式チェック後に土壌水分を再読取し、wet 判定、単回上限、24 時間累積上限の順で安全判定する。
累積上限は RTC 未導入のため Arduino 起動後 24 時間窓で管理する。
Arduino は水やり要否を判断せず、`water` 命令の安全実行可否だけを判定する。

## 返却 JSON 例

```json
{
  "status": "ok",
  "command": "water",
  "moisture_before": 41.2,
  "moisture_after": 54.8,
  "duration_ms": 3200,
  "applied_limit": false,
  "message": "watered"
}
```

`status` は次を返す。

- `uptime_ms`
- `valve_open`
- `dry_run`
- `daily_watered_ms`
- `max_single_water_ms`
- `max_daily_water_ms`
- `wet_reject_percent`
- `soil_moisture_raw`
- `soil_moisture_percent`
- `is_wet`

## 安全ロジック優先順

1. 不正コマンド拒否
2. バルブ状態初期化
3. wet 判定
4. 単回最大開放時間チェック
5. 1 日累積開放時間チェック
6. 実行
7. バルブ閉確認

# Cloud Run API詳細

| メソッド | パス | 用途 |
|------|------|------|
| `GET` | `/health` | ヘルスチェック |
| `POST` | `/judge` | 栽培判断 |
| `POST` | `/watering/effect/analyze` | 水やり効果分析 |
| `POST` | `/improve` | 第 2 回戦改善案生成 |
| `POST` | `/daily-summary` | 日次サマリー生成 |
| `POST` | `/export/research-data` | 自由研究用データ出力 |

## `POST /judge` の責務

- 観測入力の妥当性確認
- 直近履歴の取得
- Gemini 呼び出し
- JSON スキーマ検証
- `ai_decisions` 保存
- `ai_decisions` の状態遷移更新

## `POST /watering/effect/analyze` の責務

- `watering_event_id` に紐づく時系列を読む
- 上昇量、ピーク到達時間、乾燥速度を分析する
- `watering_effect_analyses` に保存する
- 次回判断に使うパラメータ候補を返す

## `POST /daily-summary` の責務

- 当日の観測、判断、実行、異常を集約する
- 親子が読める要約と、実装者向け要点の両方を返す

## `POST /export/research-data` の責務

- AI 側のログを CSV または JSON でまとめる
- 人間側記録と突き合わせやすい列構成にする

# 例外処理

- Arduino 無応答
  - 水やりを失敗として記録し、再送しない
- Arduino が拒否
  - 失敗ではなく `rejected_by_safety` として記録する
- Gemini 失敗
  - リトライ後も不可なら `decision_status=pending_manual_review`
- Firestore 保存失敗
  - ローカルキューへ退避する

# 設定フラグ案

- `ALLOW_WATER_COMMAND_FROM_PI=false`
  - Raspberry Pi から Arduino への `water` コマンド送信を既定で禁止する安全フラグ
  - 初期実装では明示的に `true` にしない限り、自動散水は実行しない
- `DRY_RUN_MODE=true`
  - Arduino 側で実バルブを開かずに机上試験する
  - 実機モードへ切り替える場合も、`ALLOW_WATER_COMMAND_FROM_PI` とは独立に確認する

# 状態遷移

## `ai_decisions`

- `proposed`
- `accepted`
- `rejected_by_safety`
- `executed`
- `failed`
- `pending_manual_review`

## `watering_events`

- `requested`
- `running`
- `success`
- `rejected_by_safety`
- `device_error`
- `communication_error`
- `effect_measuring`
- `effect_completed`

加えて `effect_measurement_status` を持つ。

- `not_started`
- `in_progress`
- `completed`
- `partial`
- `failed`

## `local_queue`

- `queued`
- `sending`
- `sent`
- `failed`
- `dead_letter`

# 実装前提の補足

- 本格実装前に Pydantic スキーマを確定する
- 画像は原本と推論用縮小版を分けて扱う
- 基本キーは `experiment_round_id` と `planter_profile_id` を全イベントに持たせる
- 比較用の追加識別子は、将来拡張が必要になった場合のみ検討する
