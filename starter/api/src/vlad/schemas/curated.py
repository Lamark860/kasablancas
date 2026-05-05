"""Схемы куратора: эксперт сохраняет 3-5 «избранных» из пула + главное дерево + заметки."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CuratedItem(BaseModel):
    """Одно растение в кураторской сборке + индивидуальная заметка эксперта."""

    plant_slug: str
    expert_note: str | None = None


class CuratedSave(BaseModel):
    """Что присылает фронт при сохранении.

    Новое API — `curated: [{plant_slug, expert_note}]`. Поле `curated_slugs`
    оставлено для backward compat (тесты, старые клиенты): если `curated` не
    задан, преобразуем `curated_slugs` в список `CuratedItem` без заметок.
    """

    curated: list[CuratedItem] | None = Field(default=None, max_length=10)
    curated_slugs: list[str] | None = Field(default=None, max_length=10)
    title_plant_slug: str | None = None
    expert_notes: str | None = None
    apply_filters: bool = True

    @model_validator(mode="after")
    def _coalesce_curated(self):
        if self.curated is None:
            self.curated = [CuratedItem(plant_slug=s) for s in (self.curated_slugs or [])]
        return self


def _normalize_curated_pool(value: Any) -> list[dict] | None:
    """Старые записи в БД хранили curated_pool как list[str]; новые — list[dict].

    Превращаем оба формата в единый list[CuratedItem-compatible-dict].
    """
    if not value:
        return None
    out: list[dict] = []
    for item in value:
        if isinstance(item, str):
            out.append({"plant_slug": item, "expert_note": None})
        elif isinstance(item, dict):
            out.append({
                "plant_slug": item["plant_slug"],
                "expert_note": item.get("expert_note"),
            })
    return out


class RecommendationOut(BaseModel):
    id: int
    person_id: int

    input_snapshot: dict
    active_oracles: list[str]
    raw_pool: list[dict]

    curated_pool: list[CuratedItem] | None = None
    title_plant_slug: str | None = None
    expert_notes: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("curated_pool", mode="before")
    @classmethod
    def _normalize(cls, v):
        return _normalize_curated_pool(v)


class RecommendationSummary(BaseModel):
    """Лёгкий вариант для истории: без raw_pool/active_oracles, только мета и кураторская выборка."""

    id: int
    person_id: int
    title_plant_slug: str | None = None
    curated_pool: list[CuratedItem] | None = None
    expert_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("curated_pool", mode="before")
    @classmethod
    def _normalize(cls, v):
        return _normalize_curated_pool(v)
