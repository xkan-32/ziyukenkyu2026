# 栽培判断プロンプト

目的:
最新観測、直近の土壌水分推移、天気、過去判断をもとに、次の行動を JSON で返す。

必須条件:

- 出力は JSON のみ
- `action` は `water` `observe_only` `manual_review` のいずれか
- `water_amount_ml` は水やり不要時は `0`
- 理由は日本語で簡潔に書く
- 不確実でも JSON 形式は崩さない
