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

## 通常観測シーケンス

1. 画像を撮影
2. サムネイルまたは縮小版を生成
3. Arduino から土壌水分値を取得
4. 天気を取得
5. 画像を GCS へ保存
6. `observations` を保存
7. 観測保存後、必要に応じて `POST /judge` を呼ぶ

## 水やりシーケンス

1. `ai_decisions` の提案 mL を受け取る
2. ローカル校正値で mL -> ms に換算する
3. `water <duration_ms>` を Arduino に送る
4. レスポンスを `watering_events` に保存する
5. `status=success` のときだけ高頻度測定を開始する

## オフライン時の扱い

- GCP 送信失敗時はローカルキューへ書く
- キュー対象
  - observation
  - watering_event
  - soil_moisture_reading
  - weather_log
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
