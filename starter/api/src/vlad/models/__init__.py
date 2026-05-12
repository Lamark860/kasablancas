"""SQLAlchemy ORM-модели.

Источник истины по структуре — handoff/02-database-schema.sql. Эти модели
повторяют его 1:1, с relationships и timestamps. Любые изменения здесь
оформляются через alembic-миграцию, не через ручной DDL.
"""
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vlad.db import Base


class TimestampMixin:
    """Стандартные created_at / updated_at для всех таблиц с историей."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Person(TimestampMixin, Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    gender: Mapped[str | None] = mapped_column(String(16))

    birth_date: Mapped[str] = mapped_column(String(10), nullable=False)  # 'YYYY-MM-DD'
    birth_time: Mapped[str | None] = mapped_column(String(5))            # 'HH:MM'
    birth_place: Mapped[str | None] = mapped_column(String(128))
    birth_lat: Mapped[float | None] = mapped_column(Float)
    birth_lon: Mapped[float | None] = mapped_column(Float)
    birth_tz: Mapped[str | None] = mapped_column(String(64))

    eye_color: Mapped[str | None] = mapped_column(String(16))

    garden_zone_usda: Mapped[int | None] = mapped_column(Integer)
    garden_region: Mapped[str | None] = mapped_column(String(128))
    garden_soil: Mapped[str | None] = mapped_column(String(16))
    garden_sun: Mapped[str | None] = mapped_column(String(16))
    garden_size_m2: Mapped[float | None] = mapped_column(Float)
    garden_style: Mapped[str | None] = mapped_column(String(64))

    notes: Mapped[str | None] = mapped_column(Text)

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="person",
        cascade="all, delete-orphan",
    )
    natal_chart: Mapped["NatalChart | None"] = relationship(
        back_populates="person",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        CheckConstraint(
            "gender IS NULL OR gender IN ('female','male','other')",
            name="ck_persons_gender",
        ),
        CheckConstraint(
            "eye_color IS NULL OR eye_color IN "
            "('blue','grey','green','hazel','brown','dark','amber')",
            name="ck_persons_eye_color",
        ),
        CheckConstraint(
            "garden_soil IS NULL OR garden_soil IN ('dry','normal','wet')",
            name="ck_persons_garden_soil",
        ),
        CheckConstraint(
            "garden_sun IS NULL OR garden_sun IN ('sun','part_shade','shade','mixed')",
            name="ck_persons_garden_sun",
        ),
    )


class Plant(TimestampMixin, Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True)

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    name_lat: Mapped[str | None] = mapped_column(String(128))
    aka: Mapped[list | None] = mapped_column(JSON)  # альтернативные имена
    category: Mapped[str] = mapped_column(String(16), nullable=False)

    min_zone_usda: Mapped[int | None] = mapped_column(Integer)
    max_zone_usda: Mapped[int | None] = mapped_column(Integer)
    shelter_friendly: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    height_max_m: Mapped[float | None] = mapped_column(Float)
    width_max_m: Mapped[float | None] = mapped_column(Float)
    growth_speed: Mapped[str | None] = mapped_column(String(16))

    sun: Mapped[str | None] = mapped_column(String(32))
    soil_moisture: Mapped[str | None] = mapped_column(String(16))
    soil_type: Mapped[str | None] = mapped_column(String(64))

    element: Mapped[str | None] = mapped_column(String(32))
    gender_energy: Mapped[str | None] = mapped_column(String(16))
    planet: Mapped[str | None] = mapped_column(String(32))
    chakra: Mapped[int | None] = mapped_column(Integer)

    bloom_months: Mapped[list | None] = mapped_column(JSON)
    bloom_color: Mapped[str | None] = mapped_column(String(64))
    autumn_color: Mapped[str | None] = mapped_column(String(64))
    evergreen: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    is_weed_like: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    hierarchy_potential: Mapped[int | None] = mapped_column(Integer)
    availability_ru: Mapped[str | None] = mapped_column(String(16))
    approx_price_rub: Mapped[int | None] = mapped_column(Integer)

    short_story: Mapped[str | None] = mapped_column(Text)
    long_story: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(256))

    __table_args__ = (
        Index("idx_plants_slug", "slug"),
        Index("idx_plants_category", "category"),
        CheckConstraint(
            "category IN ('tree','shrub','perennial','annual','grass',"
            "'fern','vine','water','bulb','succulent','herb')",
            name="ck_plants_category",
        ),
        CheckConstraint(
            "growth_speed IS NULL OR growth_speed IN ('slow','medium','fast')",
            name="ck_plants_growth_speed",
        ),
        CheckConstraint(
            "sun IS NULL OR sun IN "
            "('sun','part_shade','shade','sun_or_part_shade','any')",
            name="ck_plants_sun",
        ),
        CheckConstraint(
            "soil_moisture IS NULL OR soil_moisture IN ('dry','normal','wet','any')",
            name="ck_plants_soil_moisture",
        ),
        CheckConstraint(
            "gender_energy IS NULL OR gender_energy IN ('masculine','feminine','neutral')",
            name="ck_plants_gender_energy",
        ),
        CheckConstraint(
            "chakra IS NULL OR chakra BETWEEN 1 AND 7",
            name="ck_plants_chakra",
        ),
        CheckConstraint(
            "hierarchy_potential IS NULL OR hierarchy_potential BETWEEN 1 AND 5",
            name="ck_plants_hierarchy_potential",
        ),
        CheckConstraint(
            "availability_ru IS NULL OR availability_ru IN ('easy','medium','rare')",
            name="ck_plants_availability_ru",
        ),
    )


class Oracle(TimestampMixin, Base):
    __tablename__ = "oracles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    active: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")

    required_inputs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    sort_order: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    entries: Mapped[list["OracleEntry"]] = relationship(
        back_populates="oracle",
        cascade="all, delete-orphan",
    )


class OracleEntry(Base):
    __tablename__ = "oracle_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    oracle_id: Mapped[str] = mapped_column(
        ForeignKey("oracles.id", ondelete="CASCADE"), nullable=False
    )
    matcher: Mapped[dict] = mapped_column(JSON, nullable=False)
    plant_slug: Mapped[str] = mapped_column(
        ForeignKey("plants.slug"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    role: Mapped[str | None] = mapped_column(String(16))
    reason_for_expert: Mapped[str | None] = mapped_column(Text)
    reason_for_client: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    oracle: Mapped["Oracle"] = relationship(back_populates="entries")
    plant: Mapped["Plant"] = relationship(
        primaryjoin="OracleEntry.plant_slug == Plant.slug",
        foreign_keys="OracleEntry.plant_slug",
    )

    __table_args__ = (
        Index("idx_oracle_entries_oracle", "oracle_id"),
        Index("idx_oracle_entries_plant", "plant_slug"),
    )


class Recommendation(TimestampMixin, Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )

    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    active_oracles: Mapped[list] = mapped_column(JSON, nullable=False)
    raw_pool: Mapped[list] = mapped_column(JSON, nullable=False)

    curated_pool: Mapped[list | None] = mapped_column(JSON)
    expert_notes: Mapped[str | None] = mapped_column(Text)

    title_plant_slug: Mapped[str | None] = mapped_column(ForeignKey("plants.slug"))

    # Shareable публичная ссылка на лист гостьи — генерируется при PUT,
    # уникальная и непредсказуемая (secrets.token_urlsafe). Используется
    # на роуте GET /leaf/{token} без авторизации.
    share_token: Mapped[str | None] = mapped_column(String(48), unique=True)

    person: Mapped["Person"] = relationship(back_populates="recommendations")

    __table_args__ = (Index("idx_recommendations_person", "person_id"),)


class NatalChart(Base):
    __tablename__ = "natal_charts"

    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True
    )

    sun_sign: Mapped[str | None] = mapped_column(String(16))
    moon_sign: Mapped[str | None] = mapped_column(String(16))
    ascendant_sign: Mapped[str | None] = mapped_column(String(16))

    fire_count: Mapped[int | None] = mapped_column(Integer)
    earth_count: Mapped[int | None] = mapped_column(Integer)
    air_count: Mapped[int | None] = mapped_column(Integer)
    water_count: Mapped[int | None] = mapped_column(Integer)

    full_chart: Mapped[dict] = mapped_column(JSON, nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    person: Mapped["Person"] = relationship(back_populates="natal_chart")


__all__ = [
    "Person",
    "Plant",
    "Oracle",
    "OracleEntry",
    "Recommendation",
    "NatalChart",
]
