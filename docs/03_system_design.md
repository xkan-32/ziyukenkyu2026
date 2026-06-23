# システム構成方針

このシステムは 3 層で考えます。

- エッジ制御層: Raspberry Pi と Arduino
- クラウド判断層: Cloud Run と Vertex AI
- 永続化・研究ログ層: Firestore と Cloud Storage

# Raspberry Piの役割

- カメラ撮影
- 画像リサイズ
- Arduino との USB シリアル通信
- 観測データの組み立て
- Cloud Storage / Firestore / Cloud Run への送信
- 通常時 1 時間ごとの観測スケジュール
- 水やり後 5 分間隔の高頻度測定スケジュール
- ネットワーク断時のローカル一時保存と再送

# Arduinoの役割

- 土壌水分センサーの生値取得とパーセント換算
- ソレノイドバルブ制御
- wet 判定時の拒否
- 最大開放時間の強制
- 1 日の累積開放時間上限の強制
- 起動時、異常時、通信断時のバルブ閉
- Raspberry Pi への構造化レスポンス返却

# GCPの役割

- Cloud Storage
  - AI 側の観測画像と派生画像を保存する
- Firestore
  - 観測、判断、実行、効果測定、収穫のイベントログを保存する
- Cloud Run `agent-api`
  - AI 判断、効果分析、改善案、日次サマリー、エクスポートを扱う
- Cloud Scheduler
  - 日次サマリー、天気同期、バックアップなど低頻度バッチを起動する
- Vertex AI Gemini
  - 画像付き判断、水やり効果分析、改善案生成を行う
- Secret Manager
  - API キーなどの秘密情報を管理する

# 責務分離の要点

## Raspberry Pi と Arduino

- Raspberry Pi は「何をしたいか」を決めた結果を中継する
- Arduino は「それを安全に実行してよいか」を最終判断する
- mL から秒数への換算は初期実装では Raspberry Pi で行い、Arduino には開放時間を送る
- 理由
  - 校正や土・流量設定は Raspberry Pi / クラウド側で柔軟に変えたい
  - ただし Arduino は受け取った秒数に上限を掛ける

## Cloud とローカル

- 1 時間ごとの通常観測は、Cloud Scheduler でもできるが Raspberry Pi が主体
- 5 分間隔測定は Cloud Scheduler ではなく Raspberry Pi のローカルスケジューラ
- 理由
  - ネットワーク断でも測定を継続できる
  - 水やり直後の近接タイミングを正確に扱える

# 主要データフロー

## 観測フロー

1. Raspberry Pi が撮影する
2. Arduino から土壌水分値を取得する
3. 必要なら天気 API から気象情報を取得する
4. 画像を GCS に保存し、観測レコードを Firestore に保存する

## AI判断フロー

1. `observations` と直近履歴を agent-api に送る
2. Gemini が JSON で判断を返す
3. `ai_decisions` に保存する
4. 行動は `water`、`observe_only`、`manual_review` などで表現する

## 自動水やりフロー

1. 判断結果に `water` が含まれる
2. Raspberry Pi が希望開放時間を計算して Arduino へ送る
3. Arduino が安全判定して実行または拒否する
4. 結果を `watering_events` に保存する
5. 成功時だけ高頻度測定スケジュールを開始する

## 効果測定フロー

1. `watering_event_id` を起点に 5 分間隔ジョブを開始する
2. 12 回の測定を `soil_moisture_readings` に保存する
3. 1 時間経過後は通常観測へ戻す
4. cloud 側で `watering_effect_analyses` を生成し、次回判断の参照に使う

## 研究比較フロー

1. AI 側の観測、判断、実行、効果測定を保存する
2. 日次サマリーや CSV をエクスポートする
3. 人間側の記録と自由研究ノート上で比較する
