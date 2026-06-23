# komatsuna-ai-agent

夏休み自由研究に向けて、AI 側の小松菜栽培エージェントを構築・観測・検証するためのシステムです。

## 目的

AI（Vertex AI Gemini）と人間が同条件で小松菜を栽培し、成長・収穫結果を比較する実験を支援します。センサー・カメラ・自動水やり・クラウド連携により、観測データの記録と AI 判断を自動化します。

## 構成

| 領域 | 技術 | 役割 |
|------|------|------|
| エッジ（Raspberry Pi） | Python | カメラ撮影、GCP 連携、Arduino シリアル通信 |
| エッジ（Arduino UNO R4 WiFi） | C++ | 土壌水分読取、ソレノイドバルブ制御、安全制御 |
| クラウド（GCP） | Terraform / Cloud Run 等 | データ保存、AI 判断 API、スケジューラ |
| AI | Vertex AI Gemini | 栽培判断、効果分析、改善案生成 |

```
edge/          … Raspberry Pi・Arduino ファームウェア
services/      … Cloud Run API・バッチ処理
infra/         … Terraform（GCP リソース）
docs/          … 設計書
data/          … サンプルデータ・エクスポート
tools/         … 校正・可視化・レポート生成
```

詳細は [docs/01_overview.md](docs/01_overview.md) と [CODE.md](CODE.md) を参照してください。

## 現在の方針

- 本格実装より先に、設計・安全・データ契約を固める
- AI 判断後は、必ず効果測定まで実施して記録する
- Raspberry Pi はエッジハブ、Arduino は安全制御装置として責務を分ける
- 水道直結のため、フェイルセーフと手動停止手段を必須にする
- 人間側の判断・作業・写真・収穫結果はシステムに保存しない

## 次に実装すべき順番

1. **Arduino 安全制御** — 最大開放時間、wet 拒否、1 日上限、起動時閉止の実装と机上試験
2. **物理系検証** — リレー配線、手動バルブ、流量調整、漏水時手順の確認
3. **センサー校正** — 土壌水分センサーの乾燥・飽水校正、流量測定
4. **Raspberry Pi 基盤** — カメラ撮影、Arduino USB 通信、ローカル観測スケジューラ
5. **GCP 最小構成** — Terraform、Cloud Run `/health`、Cloud Storage、Firestore
6. **AI 判断 API** — `POST /judge` と判断ログ保存
7. **自動水やりと効果測定** — `watering_events`、高頻度測定、効果分析
8. **改善フェーズ** — 第 2 回戦改善案、日次サマリー、研究データエクスポート
