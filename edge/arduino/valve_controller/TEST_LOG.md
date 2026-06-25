# 実機確認ログ

- 実施日: 2026-06-25
- 使用ボード: Arduino UNO R4 WiFi
- 接続構成: 土壌水分センサー + MOSFETモジュール + 12V 常時閉ソレノイドバルブ

## DRY_RUN_MODE=true の確認結果

- コンパイル成功
- 書き込み成功
- `status` は 1 行 JSON で返却
- `read` は 1 行 JSON で返却
- `water 500` は成功し、dry-run 応答を返却
- `close` は `valve_open=false` を返却
- `water 100000` は `actual_duration_ms=5000` に切り詰め

代表レスポンス:

```json
{"status":"ok","command":"status","uptime_ms":17911,"valve_open":false,"dry_run":true,"daily_watered_ms":0,"max_single_water_ms":5000,"max_daily_water_ms":30000,"wet_reject_percent":75.0,"soil_moisture_raw":472,"soil_moisture_percent":0.0,"is_wet":false}
{"status":"ok","command":"read","soil_moisture_raw":472,"soil_moisture_percent":0.0,"is_wet":false}
{"status":"ok","command":"water","moisture_before_percent":0.0,"moisture_after_percent":0.0,"requested_duration_ms":500,"actual_duration_ms":500,"applied_limit":false,"dry_run":true,"message":"watered"}
{"status":"ok","command":"close","valve_open":false,"message":"valve_closed"}
{"status":"ok","command":"water","moisture_before_percent":0.0,"moisture_after_percent":0.0,"requested_duration_ms":100000,"actual_duration_ms":5000,"applied_limit":true,"dry_run":true,"message":"watered_with_limit"}
```

## DRY_RUN_MODE=false の確認結果

- コンパイル成功
- 書き込み成功
- `status` は `dry_run=false`
- `close` は毎回 `valve_open=false` を返却
- `water 300` / `water 500` / `water 1000` / `water 100000` は成功
- 電磁バルブは `water` 実行時だけ「カチッ」と動作したことをユーザーが確認
- `water 100000` は `actual_duration_ms=5000` に切り詰め
- 不正コマンドは拒否され、`valve_open=false` のまま

代表レスポンス:

```json
{"status":"ok","command":"status","uptime_ms":26026,"valve_open":false,"dry_run":false,"daily_watered_ms":0,"max_single_water_ms":5000,"max_daily_water_ms":30000,"wet_reject_percent":75.0,"soil_moisture_raw":472,"soil_moisture_percent":0.0,"is_wet":false}
{"status":"ok","command":"water","moisture_before_percent":0.0,"moisture_after_percent":0.0,"requested_duration_ms":500,"actual_duration_ms":500,"applied_limit":false,"dry_run":false,"message":"watered"}
{"status":"ok","command":"water","moisture_before_percent":0.0,"moisture_after_percent":0.5,"requested_duration_ms":100000,"actual_duration_ms":5000,"applied_limit":true,"dry_run":false,"message":"watered_with_limit"}
{"status":"error","command":"unknown","reason":"unknown_command","valve_open":false,"message":"rejected"}
{"status":"error","command":"water","reason":"invalid_duration_ms","valve_open":false,"message":"rejected"}
```

## wet拒否確認

- センサーを湿らせた状態で `read` と `water 500` を実施
- 実測値は `soil_moisture_raw=398`、`soil_moisture_percent=34.3`
- `WET_REJECT_PERCENT=75.0` に届かず `is_wet=false`
- そのため `water 500` は拒否されず実行された
- 現状の校正値では wet 拒否の実証は未完了

追加確認:

- テスト目的で一時的に `WET_REJECT_PERCENT=30.0` へ変更
- 同時に実バルブ確認のため `DRY_RUN_MODE=false` で再書き込み
- 実測値は `soil_moisture_raw=406`、`soil_moisture_percent=30.6`
- `is_wet=true` となり、`water 500` は `rejected_by_safety / soil_too_wet` で拒否
- 確認後、`WET_REJECT_PERCENT=75.0` と `DRY_RUN_MODE=true` に戻す

代表レスポンス:

```json
{"status":"ok","command":"read","soil_moisture_raw":398,"soil_moisture_percent":34.3,"is_wet":false}
{"status":"ok","command":"water","moisture_before_percent":34.3,"moisture_after_percent":33.8,"requested_duration_ms":500,"actual_duration_ms":500,"applied_limit":false,"dry_run":false,"message":"watered"}
{"status":"ok","command":"close","valve_open":false,"message":"valve_closed"}
{"status":"ok","command":"status","uptime_ms":19368,"valve_open":false,"dry_run":false,"daily_watered_ms":0,"max_single_water_ms":5000,"max_daily_water_ms":30000,"wet_reject_percent":30.0,"soil_moisture_raw":406,"soil_moisture_percent":30.6,"is_wet":true}
{"status":"ok","command":"read","soil_moisture_raw":406,"soil_moisture_percent":30.6,"is_wet":true}
{"status":"rejected_by_safety","command":"water","reason":"soil_too_wet","moisture_before_percent":30.6,"requested_duration_ms":500,"actual_duration_ms":0,"dry_run":false,"message":"rejected"}
{"status":"ok","command":"close","valve_open":false,"message":"valve_closed"}
```

## 観察結果

- close確認結果: 正常。毎回 `valve_open=false`
- 電磁バルブの動作音確認結果: `water` 実行時だけ「カチッ」を確認
- MOSFETモジュールの発熱有無: 未確認
- 12V電源の異常有無: 未確認

## 変更履歴

- `tools/attach_arduino_usb.sh`
  - `usbipd attach` が `already attached to a client` を返した場合を成功扱いに修正
  - 理由: WSL2 へ既にアタッチ済みでも `make upload` が失敗していたため
- `edge/arduino/valve_controller/config.h`
  - 実機確認時のみ `DRY_RUN_MODE=false` に変更し、確認後に `true` へ戻した

## 未実施項目

- 水道接続
- 流量測定
- Raspberry Pi連携
- MOSFETモジュールの発熱確認
- 12V電源の異常有無確認
