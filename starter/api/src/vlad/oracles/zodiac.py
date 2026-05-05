"""Оракул зодиака — растения по знаку Солнца.

Вход: Person.birth_date (плюс опционально time/place для точности на стыке знаков).
Алгоритм: берёт `chart.sun_sign` через `vlad.natal.cache.get_or_calc_chart`,
ищет в `oracle_entries` записи с matcher = {type: 'zodiac_sign', sign: ...}.

Доменный документ — research/04-zodiac-plants.md. Покрыты только те растения,
которые есть в нашем `plants.json` (это пересечение «дерево/кустарник» из
таблицы знаков и нашего справочника). Цветы и травы пока не сидируем — у нас
нет соответствующих slug'ов в plants.

Один Person → один знак Солнца → 1–4 entries (несколько растений на знак).
"""
from __future__ import annotations

from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.models import OracleEntry
from vlad.natal.cache import get_or_calc_chart

from .base import Oracle, OracleResult


class ZodiacOracle(Oracle):
    id: ClassVar[str] = "zodiac"
    name_ru: ClassVar[str] = "Знаки зодиака → растения"
    required_inputs: ClassVar[list[str]] = ["birth_date"]

    def run(self, person, db: Session) -> list[OracleResult]:
        if not self.can_run_for(person):
            return []
        chart = get_or_calc_chart(person, db)
        if chart is None:
            return []

        sun = chart.sun_sign
        entries = db.scalars(
            select(OracleEntry).where(OracleEntry.oracle_id == self.id)
        ).all()

        results: list[OracleResult] = []
        for e in entries:
            m = e.matcher or {}
            if m.get("type") != "zodiac_sign":
                continue
            if m.get("sign") != sun:
                continue
            results.append(
                OracleResult(
                    plant_slug=e.plant_slug,
                    weight=e.weight,
                    role=e.role,
                    reason_for_expert=e.reason_for_expert or "",
                    reason_for_client=e.reason_for_client or "",
                    meta={"sun_sign": sun},
                )
            )
        return results
