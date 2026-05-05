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

from vlad.models import Oracle as OracleMeta
from vlad.models import Plant
from vlad.oracles import ORACLES


def recommend(person, db: Session) -> dict[str, Any]:
    """Главная функция: Person → пул растений-кандидатов с источниками.

    Возвращает dict, готовый к JSON-сериализации:
        {
            "active_oracles": ["druid_tree", ...],
            "pool": [
                {
                    "plant_slug": "willow",
                    "plant_name_ru": "Ива",
                    "plant_short_story": "Ива — артистическая натура...",
                    "match_count": 1,
                    "total_weight": 1.0,
                    "sources": [
                        {"oracle_id": "druid_tree", "oracle_name": "...",
                         "weight": 1.0, "role": "main",
                         "reason_for_expert": "...", "reason_for_client": "..."}
                    ]
                },
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

    return {
        "active_oracles": sorted(active_meta.keys()),
        "pool": sorted_pool,
    }
