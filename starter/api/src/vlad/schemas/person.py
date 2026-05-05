"""Pydantic-схемы для Person.

Поля повторяют ORM-модель, валидация литералов даёт человекочитаемые ошибки
до того как драка дойдёт до CheckConstraint в БД.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Gender = Literal["female", "male", "other"]
EyeColor = Literal["blue", "grey", "green", "hazel", "brown", "dark", "amber"]
GardenSoil = Literal["dry", "normal", "wet"]
GardenSun = Literal["sun", "part_shade", "shade", "mixed"]


class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=64)
    middle_name: str | None = Field(None, max_length=64)
    last_name: str | None = Field(None, max_length=64)
    gender: Gender | None = None

    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    birth_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    birth_place: str | None = Field(None, max_length=128)
    birth_lat: float | None = None
    birth_lon: float | None = None
    birth_tz: str | None = Field(None, max_length=64)

    eye_color: EyeColor | None = None

    garden_zone_usda: int | None = Field(None, ge=1, le=13)
    garden_region: str | None = None
    garden_soil: GardenSoil | None = None
    garden_sun: GardenSun | None = None
    garden_size_m2: float | None = None
    garden_style: str | None = None

    notes: str | None = None


class PersonCreate(PersonBase):
    """Запрос на создание клиента."""


class PersonOut(PersonBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
