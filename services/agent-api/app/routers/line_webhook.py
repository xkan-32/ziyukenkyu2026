"""将来検討: LINE Webhook.

初期スコープでは人間側データを保存しないため未使用。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/line", tags=["future"])


# TODO: 将来スコープで必要になった場合のみ実装する
