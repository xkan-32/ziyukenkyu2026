"""ヘルスチェックルーター."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """ヘルスチェック."""
    return {"status": "ok"}
