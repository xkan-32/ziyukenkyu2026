# CODE.md

## 1. Project Mission

`komatsuna-ai-agent` の目的は、AI 側の小松菜栽培エージェントを安全に運用し、判断・実行・効果を再現可能なログとして残すことです。

成功条件は次の 4 つです。

- AI 側の観測、判断、実行、効果測定が一貫して記録されること
- AI の水やり判断後に、土壌水分変化を追跡できること
- 水道直結バルブを扱うシステムとして、危険側に倒れる設計になっていること
- 人間側の情報をシステムに保存しないこと
- 自由研究として、AI 側の記録を外部記録と比較できる形でエクスポートできること

## 2. Non-Negotiable Rules

- 水道直結のため、安全設計は機能追加より常に優先する
- AI の出力をそのままバルブ制御に直結しない
- Arduino が最終的な実行可否を判定する
- 起動時、通信断時、異常時、電源断時は必ず「バルブが閉じる側」に倒す
- 開発環境と本番環境を分け、インフラ差分は Terraform で管理する
- 秘密情報をコードや Git 管理下ファイルへ直書きしない
- LLM の判断は必ず理由付き JSON で保存する
- 判断だけで終わらせず、実行結果と効果までログに残す
- 設計と実装がずれた場合、コードだけ先に進めず関連ドキュメントも更新する

## 3. Architecture Principles

- Raspberry Pi はエッジハブ
  - カメラ、USB シリアル、ローカルスケジュール、オフライン時キューを受け持つ
- Arduino は安全制御付き実行装置
  - センサー読み取りとバルブ制御を担当し、危険な命令は拒否する
- GCP は判断と永続化
  - Firestore、Cloud Storage、Cloud Run、Vertex AI に責務を分離する
- 高頻度制御はローカル優先
  - 水やり後 5 分間隔の測定は Raspberry Pi で完結させる
- LLM は判断器であり、直接制御器ではない
  - 出力は「提案された行動」と「理由」であり、実行前に安全層を通す
- 人間側の比較記録はシステム外で管理する
  - 紙、ノート、スプレッドシート、CSV などに任せる
- すべてを因果で追えるようにする
  - `observation -> ai_decision -> watering_event -> soil_moisture_readings`

## 4. Directory Responsibilities

- `docs/`
  - 実験設計、詳細設計、安全方針、プロンプト設計を管理する
- `services/agent-api/`
  - Cloud Run 上の API。AI 判断、効果分析、改善案、日次サマリー、エクスポートを扱う
- `services/batch/`
  - 日次サマリー、天気収集、研究データ出力などの非同期バッチを置く
- `edge/raspberry-pi/`
  - 撮影、シリアル通信、GCP 送信、ローカルスケジューラを実装する
- `edge/arduino/valve_controller/`
  - センサー読み取り、バルブ制御、安全ロジックを実装する
- `infra/environments/`
  - `dev` と `prod` の Terraform エントリポイント
- `infra/modules/`
  - Storage、Firestore、Cloud Run、Scheduler などの再利用モジュール
- `data/sample/`
  - API 開発やレポート生成で使うサンプル入力
- `tools/`
  - センサー校正、流量測定、レポート生成などの支援スクリプト

## 5. Implementation Order

1. ドキュメント整備
2. Arduino 単体安全制御の確立
3. ソレノイド開閉テストと物理安全確認
4. 土壌水分センサー校正
5. Raspberry Pi カメラ撮影
6. Raspberry Pi-Arduino USB 通信
7. Raspberry Pi のローカル観測スケジューラ
8. GCP 最小構成の Terraform 化
9. Cloud Run `GET /health`
10. Cloud Storage 画像アップロード
11. Firestore 観測保存
12. Gemini による `POST /judge`
13. 自動水やり実行と `watering_events` 記録
14. 水やり後効果測定スケジューラと `soil_moisture_readings`
15. 水やり効果分析 API
16. 第 2 回戦改善案生成
17. 日次サマリー生成
18. 研究データエクスポート

## 6. Testing Strategy

- Arduino
  - `read`、`water`、異常コマンド、wet 拒否、最大開放時間制限を机上試験する
- Raspberry Pi
  - カメラ未接続、Arduino 無応答、ネットワーク断、再送キューを試験する
- agent-api
  - スキーマ検証、プロンプト出力 JSON 検証、Firestore/GCS 依存のモック試験を行う
- local queue
  - `queued -> sending -> sent` と失敗時の `failed -> dead_letter` を試験する
- Terraform
  - `fmt`、`validate`、`plan` を必須にする
- E2E
  - 観測 -> 判断 -> 水やり -> 効果測定の一連フローを dev 環境で通す
- 安全試験
  - 電源断、USB 抜去、Pi 停止、Cloud Run 障害、Arduino 再起動時の挙動を確認する

## 7. Safety Checklist

- 手動バルブが直前で閉められるか
- 流量調整バルブで最大流量を絞っているか
- 常時閉ソレノイドバルブを使用しているか
- 12V 電源容量が十分か
- 5V 系と 12V 系が分離されているか
- Raspberry Pi と Arduino が防水ボックス内に収まっているか
- 起動時にバルブ閉ログを確認したか
- 1 回の最大開放時間と 1 日の最大開放時間を設定したか
- `wet` 判定閾値と校正値が最新か
- 実験外時間に手動バルブを閉じる運用を徹底しているか

## 8. Coding Guidelines

### Python

- Pydantic スキーマを起点に入出力契約を固定する
- ルーターは薄くし、判断ロジックは `usecases/` に寄せる
- 外部 I/O は `clients/` に閉じ込め、テスト時に差し替えやすくする
- 日時はタイムゾーン付き ISO 8601 で扱う
- 人間側データを受け取る API や保存ロジックは初期スコープに含めない

### Terraform

- 環境差分は `environments/`、共通実装は `modules/` に置く
- 命名規則、ラベル、サービスアカウント権限を明示する
- いきなり本番を作らず、必ず dev で疎通確認する

### Arduino

- 安全ロジックを最上位に置き、便利機能はその下に積む
- 受信コマンドは明示的に許可したものだけ処理する
- 失敗時は沈黙せず、理由付きレスポンスを返す
- ミリ秒や閾値は `config.h` に集約する

## 9. Documentation Update Policy

- 実験ルール変更: `docs/02_experiment_design.md`
- 構成変更: `docs/03_system_design.md` と `docs/04_detail_design.md`
- Firestore/GCS スキーマ変更: `docs/05_data_design.md`
- 運用手順変更: `docs/06_operations.md`
- 安全仕様変更: `docs/07_safety.md`
- プロンプト変更: `docs/08_prompts.md` と `services/agent-api/app/prompts/`
- 実装順序や全体方針変更: `README.md` と `CODE.md`

## 10. Codex Working Rules

- 変更前に対象ファイルを読む
- 既存設計と矛盾する変更は、理由を先に文書化する
- 破壊的変更は、影響範囲を明記する
- TODO を残す場合は「何が足りず、いつ埋めるか」が分かるように書く
- 秘密情報、実在トークン、鍵は生成しない
- 実装したら、対応する設計書も同じターンで更新する
- 安全ロジックを弱める変更は、明示的な要求がない限り行わない
- 本格実装前に、まずスキーマと責務分離を固める
- 人間側データ保存につながる実装は、明示的な再スコープがあるまで追加しない
