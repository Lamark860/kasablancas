"""Оркестратор пула растений.

Прогоняет Person через все активные оракулы из реестра ORACLES, группирует
голоса по plant_slug и возвращает упорядоченный пул кандидатов. Не зависит
от FastAPI — работает с произвольным SQLAlchemy Session и Person-объектом
(подойдёт и сохранённый, и эфемерный).

Источник истины по контракту — handoff/03-oracle-interface.md.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.core.filters import apply_filters
from vlad.models import Oracle as OracleMeta
from vlad.models import Plant
from vlad.oracles import ORACLES


def recommend(person, db: Session, apply_filters_flag: bool = True) -> dict[str, Any]:
    """Главная функция: Person → пул растений-кандидатов с источниками.

    Args:
        person: SQLAlchemy Person (сохранённый или эфемерный).
        db: SQLAlchemy session.
        apply_filters_flag: если True (по умолчанию), пул прогоняется через
            фильтры эксперта (USDA, sun, soil, дерево-враг, is_weed_like).
            False — отдаём «сырой» пул, эксперт хочет видеть всё.

    Возвращает dict, готовый к JSON-сериализации:
        {
            "active_oracles": ["druid_tree", ...],
            "pool": [...],            # см. PoolEntry в schemas/recommendation.py
            "filters_applied": bool,
            "excluded": [             # пусто, если filters_applied=false
                {"plant_slug": "fig", "reason": "min USDA 7 > участка 4"},
                ...
            ]
        }

    Сортировка пула: сначала по числу пересечений, затем по сумме весов.
    """
    active_meta = {
        m.id: m
        for m in db.scalars(select(OracleMeta).where(OracleMeta.active == 1)).all()
    }

    pool: dict[str, dict] = defaultdict(
        lambda: {
            "plant_slug": None,
            "plant_name_ru": None,
            "plant_short_story": None,
            "match_count": 0,
            "total_weight": 0.0,
            "sources": [],
        }
    )

    for oracle_id, oracle in ORACLES.items():
        if oracle_id not in active_meta:
            # оракул реализован, но выключен через oracles.active=0
            continue
        oracle_meta = active_meta[oracle_id]
        for r in oracle.run(person, db):
            entry = pool[r.plant_slug]
            entry["plant_slug"] = r.plant_slug
            entry["match_count"] += 1
            entry["total_weight"] += r.weight * oracle_meta.weight
            entry["sources"].append(
                {
                    "oracle_id": oracle_id,
                    "oracle_name": oracle_meta.name_ru,
                    "weight": r.weight,
                    "role": r.role,
                    "reason_for_expert": r.reason_for_expert,
                    "reason_for_client": r.reason_for_client,
                }
            )

    # обогащаем именем и short_story из таблицы plants
    if pool:
        plants_by_slug = {
            p.slug: p
            for p in db.scalars(select(Plant).where(Plant.slug.in_(pool.keys()))).all()
        }
        for slug, entry in pool.items():
            p = plants_by_slug.get(slug)
            if p is not None:
                entry["plant_name_ru"] = p.name_ru
                entry["plant_short_story"] = p.short_story

    sorted_pool = sorted(
        pool.values(),
        key=lambda x: (x["match_count"], x["total_weight"]),
        reverse=True,
    )

    excluded: list[dict] = []
    if apply_filters_flag:
        sorted_pool, exclusions = apply_filters(sorted_pool, person, db)
        excluded = [{"plant_slug": e.plant_slug, "reason": e.reason} for e in exclusions]

    return {
        "active_oracles": sorted(active_meta.keys()),
        "pool": sorted_pool,
        "filters_applied": apply_filters_flag,
        "excluded": excluded,
    }
