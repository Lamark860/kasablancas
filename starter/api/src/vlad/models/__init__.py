"""SQLAlchemy ORM-модели. См. handoff/02-database-schema.sql для полной схемы."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vlad.db import Base


class Person(Base):
    __tablename__ = 'persons'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    gender: Mapped[str | None] = mapped_column(String(16))
    birth_date: Mapped[str] = mapped_column(String(10))   # 'YYYY-MM-DD'
    birth_time: Mapped[str | None] = mapped_column(String(5))
    birth_place: Mapped[str | None] = mapped_column(String(128))
    birth_lat: Mapped[float | None] = mapped_column(Float)
    birth_lon: Mapped[float | None] = mapped_column(Float)
    birth_tz: Mapped[str | None] = mapped_column(String(64))
    eye_color: Mapped[str | None] = mapped_column(String(16))
    garden_zone_usda: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)


class Plant(Base):
    __tablename__ = 'plants'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(128))
    name_lat: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32))
    min_zone_usda: Mapped[int | None] = mapped_column(Integer)
    element: Mapped[str | None] = mapped_column(String(32))
    is_weed_like: Mapped[int] = mapped_column(Integer, default=0)
    hierarchy_potential: Mapped[int | None] = mapped_column(Integer)
    short_story: Mapped[str | None] = mapped_column(Text)
    long_story: Mapped[str | None] = mapped_column(Text)


class Oracle(Base):
    __tablename__ = 'oracles'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name_ru: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[int] = mapped_column(Integer, default=1)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    required_inputs: Mapped[list] = mapped_column(JSON, default=list)


class OracleEntry(Base):
    __tablename__ = 'oracle_entries'
    id: Mapped[int] = mapped_column(primary_key=True)
    oracle_id: Mapped[str] = mapped_column(ForeignKey('oracles.id'), index=True)
    matcher: Mapped[dict] = mapped_column(JSON)
    plant_slug: Mapped[str] = mapped_column(String(64), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    role: Mapped[str | None] = mapped_column(String(16))
    reason_for_expert: Mapped[str | None] = mapped_column(Text)
    reason_for_client: Mapped[str | None] = mapped_column(Text)
