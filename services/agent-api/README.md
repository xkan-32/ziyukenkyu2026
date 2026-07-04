# services/agent-api

このディレクトリは Cloud Run 上の AI 側 API を置く。

初期スコープで使用するのは主に次です。

- `GET /health`
- 将来の `POST /judge`
- 将来の `POST /watering/effect/analyze`
- 将来の研究データエクスポート関連

次のファイルやモジュールは現時点では初期スコープ外であり、使用しない。

- `app/routers/line_webhook.py`
- `app/schemas/human_task.py`
- `app/schemas/verification.py`
- `app/usecases/create_human_task.py`
- `app/usecases/verify_human_task.py`
- `app/clients/line_client.py`
- `app/prompts/verify_task.md`

これらは将来検討用の残置であり、初期スコープでは有効化しない。人間側の判断、作業、写真、収穫結果を保存する用途には使わない。
