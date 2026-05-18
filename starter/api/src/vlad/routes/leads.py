"""Лиды с публичной анкеты.

Создаются анонимно из `pages/index.vue` после галки «хочу консультацию».
В админке к ним прикасается эксперт — меняет status, добавляет notes.
"""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import get_db
from vlad.models import Lead
from vlad.schemas.lead import LeadCreate, LeadOut, LeadStats

router = APIRouter()


@router.post("/", response_model=LeadOut, status_code=http_status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> Lead:
    data = payload.model_dump()
    # companions — список pydantic-моделей, преобразуем в plain dicts, чтобы JSON-колонка не ругалась
    if data.get("companions"):
        data["companions"] = [c if isinstance(c, dict) else c.model_dump() for c in data["companions"]]
    lead = Lead(**data)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/", response_model=list[LeadOut])
def list_leads(
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Lead]:
    """Список лидов для админки. Фильтр по status (?status=new|contacted|won|lost)."""
    q = select(Lead).order_by(Lead.created_at.desc())
    if status:
        q = q.where(Lead.status == status)
    return db.scalars(q).all()


@router.get("/stats", response_model=LeadStats)
def lead_stats(db: Session = Depends(get_db)) -> LeadStats:
    """Сводка по лидам — для админ-дашборда."""
    leads = db.scalars(select(Lead)).all()
    by_status = Counter(l.status for l in leads)
    by_city = Counter(l.city for l in leads if l.city)
    return LeadStats(
        total=len(leads),
        with_consultation=sum(1 for l in leads if l.want_consultation),
        by_status=dict(by_status),
        by_city=sorted(by_city.items(), key=lambda x: x[1], reverse=True),
    )


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "lead not found")
    return lead
