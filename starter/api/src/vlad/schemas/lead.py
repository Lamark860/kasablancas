"""Pydantic-схемы для /leads.

Входная LeadCreate приходит с публичной анкеты (`pages/index.vue`) после того,
как гостья поставила галку «хочу консультацию» и оставила контакт. На выходе —
LeadOut для админки, поддерживает status (workflow) и notes (заметки эксперта).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


LeadStatus = Literal["new", "contacted", "won", "lost"]
EyeColor = Literal["blue", "grey", "green", "hazel", "brown", "dark", "amber"]


class CompanionSnapshot(BaseModel):
    slug: str
    name_ru: str | None = None
    match_count: int | None = None


class LeadCreate(BaseModel):
    contact: str = Field(..., min_length=1, max_length=128)
    want_consultation: bool = True

    first_name: str = Field(..., min_length=1, max_length=64)
    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    birth_place: str | None = Field(None, max_length=128)
    birth_lat: float | None = None
    birth_lon: float | None = None
    birth_tz: str | None = Field(None, max_length=64)
    eye_color: EyeColor | None = None

    main_plant_slug: str | None = Field(None, max_length=64)
    main_plant_name: str | None = Field(None, max_length=128)
    companions: list[CompanionSnapshot] | None = None

    city: str | None = Field(None, max_length=64)
    source: dict[str, Any] | None = None


class LeadOut(LeadCreate):
    id: int
    status: LeadStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadStats(BaseModel):
    """Лёгкие цифры для дашборда. Пока без графиков — просто счётчики."""

    total: int
    with_consultation: int
    by_status: dict[str, int]
    by_city: list[tuple[str, int]]  # отсортирован по убыванию
