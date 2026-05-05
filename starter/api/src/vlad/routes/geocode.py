"""Геокодирование места рождения для UI /intake (F1).

Эксперт вводит «Москва» → blur → фронт дёргает GET /geocode?q=Москва →
получает список кандидатов с label для disambiguation. Если 0 — ошибка
ввода; если 1 — автоподстановка; если 2+ — выбор пользователем.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from vlad.natal.geocode import search_places


router = APIRouter()


class GeocodeCandidate(BaseModel):
    lat: float
    lon: float
    tz: str | None = None
    label: str | None = None


@router.get("/", response_model=list[GeocodeCandidate])
def geocode(
    q: str = Query(..., min_length=1, description="Название места: «Москва», «Saint-Petersburg»."),
    limit: int = Query(5, ge=1, le=10, description="Сколько кандидатов вернуть."),
):
    """Поиск кандидатов через Nominatim/OSM.

    Пустой список означает «не найдено» (Nominatim ничего не вернул)
    или сбой сети (логируется бэком, для UI это та же ситуация — невалидный ввод).
    """
    return search_places(q, limit=limit)
