"""Pydantic-схемы для /recommend.

Вход: либо id уже сохранённого Person, либо набор полей напрямую (одноразовый
расчёт без записи в БД). Не оба сразу.

Выход: пул растений с источниками каждого голоса.
"""
from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from .person import PersonCreate


class OracleSource(BaseModel):
    oracle_id: str
    oracle_name: str
    weight: float
    role: str | None = None
    reason_for_expert: str = ""
    reason_for_client: str = ""


class PoolEntry(BaseModel):
    plant_slug: str
    plant_name_ru: str | None = None
    plant_short_story: str | None = None
    match_count: int
    total_weight: float
    sources: list[OracleSource]
    notes: list[str] = []   # пометки фильтров (например 'weed_like — вес снижен')


class Exclusion(BaseModel):
    plant_slug: str
    reason: str


class RecommendInput(BaseModel):
    """Либо person_id (взять Person из БД), либо inline-объект person."""

    person_id: int | None = None
    person: PersonCreate | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.person_id is None) == (self.person is None):
            raise ValueError("укажите ровно одно: person_id ИЛИ person")
        return self


class RecommendOutput(BaseModel):
    active_oracles: list[str]
    pool: list[PoolEntry]
    filters_applied: bool
    excluded: list[Exclusion] = []

    model_config = ConfigDict(from_attributes=True)
