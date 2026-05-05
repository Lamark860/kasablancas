"""Фильтры эксперта поверх пула оракулов.

Применяются после оркестратора (`recommend`), когда пул уже собран. Каждый
фильтр — отдельная функция, чтобы их можно было включать/выключать
независимо. На MVP-этапе включается всё или ничего через параметр
`apply_filters` у `POST /recommend`.

Источники:
- USDA / sun / soil — `research/08-climate-zones.md`.
- «Дерево-враг» — `research/02-druid-tree-calendar.md` (раздел «Дерево-враг»).

Логика на «не моё» дерево: если период этого растения в `druid_tree`
пересекается с интервалом ±40 дней от даты рождения и при этом это не
наше собственное дерево — растение считается «враждебным» и исключается.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.models import OracleEntry, Plant


ENEMY_WINDOW_DAYS = 40
WEED_WEIGHT_FACTOR = 0.5  # is_weed_like — не выкидываем, понижаем вес


@dataclass
class Exclusion:
    plant_slug: str
    reason: str


def _sun_compatible(person_sun: str, plant_sun: str | None) -> bool:
    """Plant.sun ∈ {sun, part_shade, shade, sun_or_part_shade, any}.
    Person.garden_sun ∈ {sun, part_shade, shade, mixed}.
    None у растения — фильтр не срабатывает (нет данных).
    """
    if plant_sun is None:
        return True
    if plant_sun == "any" or person_sun == "mixed":
        return True
    if plant_sun == person_sun:
        return True
    if plant_sun == "sun_or_part_shade" and person_sun in ("sun", "part_shade"):
        return True
    return False


def _soil_compatible(person_soil: str, plant_soil: str | None) -> bool:
    """Plant.soil_moisture ∈ {dry, normal, wet, any}; Person.garden_soil ∈ {dry, normal, wet}."""
    if plant_soil is None:
        return True
    if plant_soil == "any":
        return True
    return plant_soil == person_soil


def _in_range(mmdd: str, start: str, end: str) -> bool:
    if start <= end:
        return start <= mmdd <= end
    return mmdd >= start or mmdd <= end


def enemy_tree_slugs(birth_date_iso: str, db: Session) -> set[str]:
    """Slug'и деревьев из druid_tree, чьи периоды пересекаются с ±40 днями
    от даты рождения, кроме «своего» дерева.

    Если birth_date невалиден — возвращает пустое множество (фильтр становится no-op).
    """
    try:
        bd = datetime.fromisoformat(birth_date_iso).date()
    except (ValueError, TypeError):
        return set()

    enemy_dates = set()
    for delta in range(-ENEMY_WINDOW_DAYS, ENEMY_WINDOW_DAYS + 1):
        enemy_dates.add((bd + timedelta(days=delta)).strftime("%m-%d"))

    bd_mmdd = bd.strftime("%m-%d")

    entries = db.scalars(
        select(OracleEntry).where(OracleEntry.oracle_id == "druid_tree")
    ).all()

    own_slugs: set[str] = set()
    for e in entries:
        m = e.matcher or {}
        if m.get("type") != "date_range_yearly":
            continue
        start, end = m.get("from"), m.get("to")
        if start and end and _in_range(bd_mmdd, start, end):
            own_slugs.add(e.plant_slug)

    enemies: set[str] = set()
    for e in entries:
        if e.plant_slug in own_slugs:
            continue
        m = e.matcher or {}
        if m.get("type") != "date_range_yearly":
            continue
        start, end = m.get("from"), m.get("to")
        if not start or not end:
            continue
        for d in enemy_dates:
            if _in_range(d, start, end):
                enemies.add(e.plant_slug)
                break
    return enemies


def apply_filters(pool: list[dict], person, db: Session) -> tuple[list[dict], list[Exclusion]]:
    """Возвращает (отфильтрованный_пул, список_исключений).

    Каждое исключение содержит slug и причину; пул перевзвешивается
    (is_weed_like понижает total_weight) и пере-сортируется.
    """
    if not pool:
        return pool, []

    plant_slugs = [e["plant_slug"] for e in pool]
    plants_by_slug = {
        p.slug: p
        for p in db.scalars(select(Plant).where(Plant.slug.in_(plant_slugs))).all()
    }

    # «дерево-враг» считаем один раз
    birth_date = (getattr(person, "birth_date", None) or "").strip()
    enemies = enemy_tree_slugs(birth_date, db) if birth_date else set()

    person_zone = getattr(person, "garden_zone_usda", None)
    person_sun = getattr(person, "garden_sun", None)
    person_soil = getattr(person, "garden_soil", None)

    kept: list[dict] = []
    excluded: list[Exclusion] = []

    for entry in pool:
        slug = entry["plant_slug"]
        plant = plants_by_slug.get(slug)

        if slug in enemies:
            excluded.append(Exclusion(slug, f"дерево-враг (±{ENEMY_WINDOW_DAYS} дней по друидам)"))
            continue

        if plant is not None:
            if (
                person_zone is not None
                and plant.min_zone_usda is not None
                and plant.min_zone_usda > person_zone
            ):
                excluded.append(
                    Exclusion(
                        slug,
                        f"min USDA {plant.min_zone_usda} > участка {person_zone}",
                    )
                )
                continue

            if person_sun and not _sun_compatible(person_sun, plant.sun):
                excluded.append(Exclusion(slug, f"sun {plant.sun} ≠ {person_sun}"))
                continue

            if person_soil and not _soil_compatible(person_soil, plant.soil_moisture):
                excluded.append(
                    Exclusion(slug, f"soil {plant.soil_moisture} ≠ {person_soil}")
                )
                continue

            if plant.is_weed_like:
                entry = {**entry, "total_weight": entry["total_weight"] * WEED_WEIGHT_FACTOR}
                entry.setdefault("notes", []).append("weed_like — вес снижен")

        kept.append(entry)

    kept.sort(key=lambda x: (x["match_count"], x["total_weight"]), reverse=True)
    return kept, excluded
