from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def recommend():
    """Главный эндпоинт: на входе Person, на выходе пул растений."""
    # TODO: вызвать orchestrator.recommend(person, db)
    return {"pool": []}
