# Firestore コレクション設計

このプロジェクトでは、後から「なぜそうなったか」を追えるようにイベント中心で保存します。

共通フィールドの基本方針:

- `id`
- `experiment_round_id`
- `planter_profile_id`
- `created_at` または `occurred_at`
- `source`

## 1. observations

### 責務

- ある時点の観測スナップショット
- AI 判断の主要入力

### 主なフィールド

- `observed_at`
- `image_gcs_path`
- `thumbnail_gcs_path`
- `soil_moisture_percent`
- `soil_moisture_raw`
- `temperature_c`
- `humidity_percent`
- `weather_summary`
- `observation_type`
  - `scheduled`
  - `post_watering`
  - `manual`

### JSON例

```json
{
  "id": "obs_20260622_120000_ai",
  "experiment_round_id": "round_1",
  "planter_profile_id": "ai_planter_a",
  "observed_at": "2026-06-22T12:00:00+09:00",
  "observation_type": "scheduled",
  "image_gcs_path": "gs://komatsuna-ai-agent-dev/images/ai/2026/06/22/120000.jpg",
  "thumbnail_gcs_path": "gs://komatsuna-ai-agent-dev/images/ai/2026/06/22/120000_small.jpg",
  "soil_moisture_raw": 612,
  "soil_moisture_percent": 42.5,
  "temperature_c": 26.3,
  "humidity_percent": 55.0,
  "weather_summary": "cloudy",
  "source": "raspberry_pi"
}
```

### インデックス候補

- `experiment_round_id + observed_at desc`
- `planter_profile_id + observed_at desc`

## 2. ai_decisions

### 責務

- AI がどの観測を見て、どう判断したかを残す

### 主なフィールド

- `observation_id`
- `action`
- `water_amount_ml`
- `requested_duration_ms`
- `reason`
- `confidence`
- `decision_status`

### JSON例

```json
{
  "id": "dec_20260622_120500_ai",
  "experiment_round_id": "round_1",
  "planter_profile_id": "ai_planter_a",
  "decided_at": "2026-06-22T12:05:00+09:00",
  "observation_id": "obs_20260622_120000_ai",
  "action": "water",
  "water_amount_ml": 35,
  "requested_duration_ms": 3200,
  "reason": "土壌水分が低く、葉の張りも弱い",
  "confidence": 0.85,
  "decision_status": "proposed",
  "model": "gemini-2.5-flash"
}
```

### 状態遷移

- `proposed`
- `accepted`
- `rejected_by_safety`
- `executed`
- `failed`
- `pending_manual_review`

### インデックス候補

- `observation_id`
- `planter_profile_id + decided_at desc`

## 3. watering_events

### 責務

- 水やり指示の実行結果と安全判定の記録

### 主なフィールド

- `decision_id`
- `requested_duration_ms`
- `actual_duration_ms`
- `requested_amount_ml`
- `soil_moisture_before`
- `soil_moisture_after`
- `status`
  - `success`
  - `rejected_by_safety`
  - `device_error`
  - `communication_error`
- `rejection_reason`
- `arduino_response`
- `effect_measurement_status`
- `expected_effect_measurements`
- `completed_effect_measurements`

### JSON例

```json
{
  "id": "we_20260622_120600_ai",
  "experiment_round_id": "round_1",
  "planter_profile_id": "ai_planter_a",
  "started_at": "2026-06-22T12:06:00+09:00",
  "ended_at": "2026-06-22T12:06:03+09:00",
  "decision_id": "dec_20260622_120500_ai",
  "requested_amount_ml": 35,
  "requested_duration_ms": 3200,
  "actual_duration_ms": 3200,
  "soil_moisture_before": 42.5,
  "soil_moisture_after": 54.8,
  "status": "success",
  "effect_measurement_status": "in_progress",
  "expected_effect_measurements": 12,
  "completed_effect_measurements": 1,
  "rejection_reason": null,
  "arduino_response": {
    "status": "ok",
    "command": "water",
    "duration_ms": 3200,
    "message": "watered"
  }
}
```

### 状態遷移

- `requested`
- `running`
- `success`
- `rejected_by_safety`
- `device_error`
- `communication_error`
- `effect_measuring`
- `effect_completed`

### 効果測定状態

- `not_started`
- `in_progress`
- `completed`
- `partial`
- `failed`

### インデックス候補

- `decision_id`
- `status + started_at desc`
- `planter_profile_id + started_at desc`

## 4. soil_moisture_readings

### 責務

- 水やり効果測定を含む土壌水分の時系列ログ

### 主なフィールド

- `watering_event_id`
- `read_at`
- `measurement_phase`
  - `baseline`
  - `post_watering`
  - `normal_hourly`
- `minutes_after_watering`
- `sequence_no`

### JSON例

```json
{
  "id": "smr_20260622_121100_ai",
  "experiment_round_id": "round_1",
  "planter_profile_id": "ai_planter_a",
  "read_at": "2026-06-22T12:11:00+09:00",
  "watering_event_id": "we_20260622_120600_ai",
  "measurement_phase": "post_watering",
  "sequence_no": 1,
  "minutes_after_watering": 5,
  "soil_moisture_raw": 691,
  "soil_moisture_percent": 58.2
}
```

### インデックス候補

- `watering_event_id + read_at asc`
- `planter_profile_id + read_at desc`

## 5. watering_effect_analyses

### 責務

- 水やり後の時系列を分析し、効果をまとめる

### 主なフィールド

- `watering_event_id`
- `analysis_status`
- `peak_moisture_percent`
- `minutes_to_peak`
- `moisture_delta_percent`
- `drying_rate_per_hour`
- `recommendation`

### JSON例

```json
{
  "id": "wea_20260622_130500_ai",
  "experiment_round_id": "round_1",
  "planter_profile_id": "ai_planter_a",
  "created_at": "2026-06-22T13:05:00+09:00",
  "watering_event_id": "we_20260622_120600_ai",
  "analysis_status": "completed",
  "peak_moisture_percent": 58.2,
  "minutes_to_peak": 15,
  "moisture_delta_percent": 15.7,
  "drying_rate_per_hour": 2.1,
  "recommendation": "次回も30-40mlを基準にする"
}
```

### インデックス候補

- `watering_event_id`
- `created_at desc`

## 6. device_status

### 責務

- デバイスの稼働状態を追跡する

### 主なフィールド

- `device_type`
- `recorded_at`
- `status`
- `details`

### JSON例

```json
{
  "id": "ds_20260622_120000_pi",
  "device_type": "raspberry_pi",
  "recorded_at": "2026-06-22T12:00:00+09:00",
  "status": "healthy",
  "details": {
    "disk_free_mb": 8120,
    "network": "online"
  }
}
```

### インデックス候補

- `device_type + recorded_at desc`

## 7. safety_events

### 責務

- 安全拒否、緊急停止、異常系イベントを保存する

### 主なフィールド

- `event_type`
- `recorded_at`
- `severity`
- `message`
- `related_watering_event_id`

### JSON例

```json
{
  "id": "se_20260622_120601_ai",
  "recorded_at": "2026-06-22T12:06:01+09:00",
  "event_type": "rejected_by_safety",
  "severity": "warning",
  "message": "soil too wet",
  "related_watering_event_id": "we_20260622_120600_ai"
}
```

### インデックス候補

- `event_type + recorded_at desc`
- `severity + recorded_at desc`

## 8. harvest_results

### 責務

- 収穫時の比較結果

### 主なフィールド

- `harvested_at`
- `round`
- `total_weight_g`
- `average_weight_g`
- `average_height_cm`
- `average_leaf_count`
- `appearance_score`
- `taste_score`

### JSON例

```json
{
  "id": "hr_20260825_ai_round2",
  "experiment_round_id": "round_2",
  "planter_profile_id": "ai_planter_a",
  "round": 2,
  "harvested_at": "2026-08-25T10:00:00+09:00",
  "total_weight_g": 320.5,
  "average_weight_g": 40.1,
  "average_height_cm": 21.4,
  "average_leaf_count": 8.2,
  "appearance_score": 4,
  "taste_score": 4,
  "image_gcs_paths": [
    "gs://komatsuna-ai-agent-dev/harvest/ai/20260825_01.jpg"
  ],
  "notes": "虫食いは少ない"
}
```

### インデックス候補

- `experiment_round_id + harvested_at desc`

## 追加提案コレクション

## 9. weather_logs

- 判断時に参照した天気を保存し、後で再現可能にする

## 10. calibration_profiles

- センサー校正値、流量係数、適用期間を保存する

## 11. experiment_rounds

- 第 1 回戦、第 2 回戦の期間、条件、メモを保存する

## 12. planter_profiles

- プランターごとの土、鉢サイズ、設置場所、系統を保存する
