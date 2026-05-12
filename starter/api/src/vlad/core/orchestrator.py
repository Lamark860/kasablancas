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


def recommend(
    person,
    db: Session,
    apply_filters_flag: bool = True,
    disabled_oracles: set[str] | None = None,
    *,
    frost: bool | None = None,
    hide_weeds: bool | None = None,
) -> dict[str, Any]:
    """Главная функция: Person → пул растений-кандидатов с источниками.

    Args:
        person: SQLAlchemy Person (сохранённый или эфемерный).
        db: SQLAlchemy session.
        apply_filters_flag: backward-compat — если True, оба фильтра on;
            если False, оба off. Новый код должен передавать frost/hide_weeds
            явно; этот флаг игнорируется когда заданы оба новых.
        frost: фильтр «выживет в саду» — USDA, sun, soil, дерево-враг.
            None → подтянуть из apply_filters_flag.
        hide_weeds: фильтр «приглушить сорные» — is_weed_like ×0.5.
            None → подтянуть из apply_filters_flag.
        disabled_oracles: оракулы, которые эксперт временно выключил в UI
            (fontes-тогглы). На уровне БД они остаются active=1; здесь
            пропускаем их при сборке пула, чтобы UI мог делать «что если?».

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

    disabled = disabled_oracles or set()
    for oracle_id, oracle in ORACLES.items():
        if oracle_id not in active_meta:
            # оракул реализован, но выключен через oracles.active=0
            continue
        if oracle_id in disabled:
            # эксперт выключил оракул через fontes-тоггл — не учитываем
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

    # Разрешаем флаги: явные frost/hide_weeds приоритетнее, иначе наследуем
    # от apply_filters_flag (backward compat для существующих вызовов и тестов).
    effective_frost = apply_filters_flag if frost is None else frost
    effective_hide_weeds = apply_filters_flag if hide_weeds is None else hide_weeds

    excluded: list[dict] = []
    if effective_frost or effective_hide_weeds:
        sorted_pool, exclusions = apply_filters(
            sorted_pool, person, db,
            frost=effective_frost,
            hide_weeds=effective_hide_weeds,
        )
        excluded = [{"plant_slug": e.plant_slug, "reason": e.reason} for e in exclusions]

    return {
        "active_oracles": sorted(active_meta.keys() - disabled),
        "pool": sorted_pool,
        "filters_applied": effective_frost or effective_hide_weeds,
        "frost": effective_frost,
        "hide_weeds": effective_hide_weeds,
        "excluded": excluded,
    }
