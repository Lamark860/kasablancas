"""Заглушки роутов — наполняй по ходу разработки."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_persons():
    # TODO: реализовать
    return []


@router.post("/")
def create_person():
    # TODO: реализовать
    return {"id": 1}
