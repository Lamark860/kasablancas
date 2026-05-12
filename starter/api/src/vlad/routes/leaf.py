"""Публичный shareable-роут листа гостьи: GET /leaf/{token}.

Токен непредсказуем (32 байта url-safe), генерируется при PUT
`/persons/{id}/recommendation`. Endpoint не требует авторизации —
эксперт отдаёт ссылку клиентке как есть, вместе с PDF.

PDF продолжает жить на /reports/{person_id}.pdf и доступен через тот
же токен косвенно: фронт берёт rec.person_id из leaf-ответа и подкачивает
PDF. В рамках фазы 1 это нормально; для полной публичной модели в
будущем сделаем /reports/by-token/{token}.pdf.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import get_db
from vlad.models import Recommendation
from vlad.schemas.curated import RecommendationOut

router = APIRouter()


@router.get("/{token}", response_model=RecommendationOut)
def get_leaf_by_token(token: str, db: Session = Depends(get_db)):
    rec = db.scalars(
        select(Recommendation).where(Recommendation.share_token == token)
    ).first()
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "leaf not found")
    return rec
