"""Нумерология имени по Пифагору (русский алфавит).

Сумма позиций букв (по таблице из research/07) → редукция до одной цифры
1..9 → растения этого числа. Мастер-числа (11, 22, 33) сводятся к 1, 4, 6
соответственно — для наших целей этого достаточно.

Сопоставление число → растение взято из research/07-other-systems.md,
ограничено растениями, доступными в plants.json. Семёрка («мистика») в
research указывает можжевельник/тис/папоротник — у нас их нет, ставим
кипарис как ближайший вечнозелёный «эзотерический» аналог.
"""
from __future__ import annotations

from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.models import OracleEntry

from .base import Oracle, OracleResult


# а=1, б=2, в=3, ... — таблица Пифагора в кириллической раскладке
_PYTHAGOREAN = {
    "а": 1, "б": 2, "в": 3, "г": 4, "д": 5, "е": 6, "ё": 7, "ж": 8, "з": 9,
    "и": 1, "й": 2, "к": 3, "л": 4, "м": 5, "н": 6, "о": 7, "п": 8, "р": 9,
    "с": 1, "т": 2, "у": 3, "ф": 4, "х": 5, "ц": 6, "ч": 7, "ш": 8, "щ": 9,
    "ъ": 1, "ы": 2, "ь": 3, "э": 4, "ю": 5, "я": 6,
}


def name_number(name: str) -> int | None:
    """Сумма букв имени, редуцированная до 1..9. None для пустого имени."""
    s = sum(_PYTHAGOREAN.get(ch, 0) for ch in (name or "").lower() if ch.isalpha())
    if s == 0:
        return None
    while s > 9:
        s = sum(int(d) for d in str(s))
    return s


class NumerologyOracle(Oracle):
    id: ClassVar[str] = "numerology"
    name_ru: ClassVar[str] = "Нумерология имени → растение"
    required_inputs: ClassVar[list[str]] = ["first_name"]

    def run(self, person, db: Session) -> list[OracleResult]:
        if not self.can_run_for(person):
            return []
        n = name_number(getattr(person, "first_name", "") or "")
        if n is None:
            return []

        entries = db.scalars(
            select(OracleEntry).where(OracleEntry.oracle_id == self.id)
        ).all()
        results: list[OracleResult] = []
        for e in entries:
            m = e.matcher or {}
            if m.get("type") != "name_pythagorean_number":
                continue
            if m.get("number") != n:
                continue
            results.append(
                OracleResult(
                    plant_slug=e.plant_slug,
                    weight=e.weight,
                    role=e.role,
                    reason_for_expert=e.reason_for_expert or "",
                    reason_for_client=e.reason_for_client or "",
                    meta={"name_number": n},
                )
            )
        return results
