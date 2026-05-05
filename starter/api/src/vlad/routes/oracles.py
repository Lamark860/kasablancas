from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_oracles():
    """Список оракулов (метаданные + статус active)."""
    return []
