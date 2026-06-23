# プロンプト設計

このプロジェクトでは、LLM に自由文を返させるのではなく、必ず JSON を返させます。理由は次のとおりです。

- API レスポンスとして機械処理しやすい
- Firestore にそのまま保存しやすい
- 後で研究ログとして比較しやすい

実体ファイルは `services/agent-api/app/prompts/` に置き、ここでは役割と JSON 契約を定義します。

# 共通ルール

- 出力は JSON のみ
- 余計な説明文や Markdown を禁止する
- 不確実な場合は推測で断定せず、`unable_to_determine` 系の値を返す
- 理由フィールドは短すぎず、後で人が読んで判断経緯を追える長さにする

# 1. 栽培判断プロンプト

- ファイル: `app/prompts/judge.md`
- 用途: 最新観測、画像、天気、履歴から次の行動を決める

## 出力 JSON スキーマ案

```json
{
  "action": "water",
  "water_amount_ml": 35,
  "urgency": "medium",
  "reason": "土壌水分が低く、葉の張りも弱い",
  "confidence": 0.85
}
```

# 2. 水やり判断プロンプト

- 栽培判断の中に含めてもよいが、将来分離しやすいように論理上は独立させる
- 用途: 水やり量と緊急度の細分化

## 出力 JSON スキーマ案

```json
{
  "should_water": true,
  "recommended_amount_ml": 35,
  "reason": "乾燥が進んでいる",
  "confidence": 0.83
}
```

# 3. 水やり効果分析プロンプト

- ファイル: `app/prompts/watering_effect.md`
- 用途: 水やり前後の時系列を見て、効き方を分析する

## 出力 JSON スキーマ案

```json
{
  "effect_summary": "適切に上昇した",
  "peak_moisture_percent": 58.2,
  "minutes_to_peak": 15,
  "drying_trend": "moderate",
  "next_recommendation": "次回も30-40mlを基準にする",
  "confidence": 0.8
}
```

# 4. 2回戦改善案プロンプト

- ファイル: `app/prompts/improvement.md`
- 用途: 第 1 回戦のログと収穫結果から改善案を出す

## 出力 JSON スキーマ案

```json
{
  "summary": "水やり量のばらつきを減らすべき",
  "issues": [
    "乾燥後の回復が遅い"
  ],
  "actions": [
    "初期水やり量を10ml増やす"
  ],
  "prompt_adjustments": [
    "葉の張りより土壌水分推移を優先する"
  ]
}
```

# 5. 日次サマリープロンプト

- 用途: その日の観測、判断、水やり、効果測定、異常を親子向けに要約する

## 出力 JSON スキーマ案

```json
{
  "date": "2026-07-05",
  "summary": "AI側は午後に1回水やりした",
  "highlights": [
    "土壌水分は15分後にピーク"
  ],
  "alerts": [
    "15時の観測送信が再送待ち"
  ]
}
```

# 実装上の注意

- プロンプト本文には、許可される列挙値を明記する
- 数値の単位を明示する
- JSON バリデーション失敗時の再プロンプト戦略を `usecases/` 側で持つ
- モデル更新時は、期待 JSON が崩れていないかサンプルで確認する
- 人間側の入力やシステム内報告フローを前提にしたプロンプトは初期スコープから外す
