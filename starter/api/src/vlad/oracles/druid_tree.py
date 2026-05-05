"""Кельтский гороскоп друидов — деревья.

Доменный документ: research/02-druid-tree-calendar.md.
Контракт: handoff/03-oracle-interface.md.

Сидинг entries — data/seed/druid-tree.json. Каждая запись — один период
с матчером {type: 'date_range_yearly', from: 'MM-DD', to: 'MM-DD'}.
Эта реализация поддерживает только этот тип матчера; остальные типы тихо
игнорируются (на случай если в JSON попадёт чужая запись).

Особенности доменки:
- 22 знака; 18 из них имеют по два периода в году (весна-лето / осень-зима),
  4 одиночных (Дуб 21.03, Берёза 24.06, Олива 23.09, Бук 22.12).
- День 21.12 в источнике research/02 не покрыт ни одним знаком — оракул для
  такой даты вернёт пустой результат. Это намеренно (см. WORK_LOG, этап 2).
- "Дерево-враг" (40 дней до/после) пока не реализовано — это фильтр этапа 6.
- Поправка по дате зачатия — опциональное поле, тоже на потом.
"""
from __future__ import annotations

from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.models import OracleEntry

from .base import Oracle, OracleResult


class DruidTreeOracle(Oracle):
    id: ClassVar[str] = "druid_tree"
    name_ru: ClassVar[str] = "Кельтский гороскоп друидов (деревья)"
    required_inputs: ClassVar[list[str]] = ["birth_date"]

    def run(self, person, db: Session) -> list[OracleResult]:
        if not self.can_run_for(person):
            return []

        bd = (person.birth_date or "").strip()
        # 'YYYY-MM-DD' → берём 'MM-DD'
        if len(bd) < 10 or bd[4] != "-" or bd[7] != "-":
            return []
        mmdd = bd[5:10]

        entries = db.scalars(
            select(OracleEntry).where(OracleEntry.oracle_id == self.id)
        ).all()

        results: list[OracleResult] = []
        for e in entries:
            m = e.matcher or {}
            if m.get("type") != "date_range_yearly":
                continue
            start, end = m.get("from"), m.get("to")
            if not start or not end:
                continue
            if self._in_range(mmdd, start, end):
                results.append(
                    OracleResult(
                        plant_slug=e.plant_slug,
                        weight=e.weight,
                        role=e.role,
                        reason_for_expert=e.reason_for_expert or "",
                        reason_for_client=e.reason_for_client or "",
                        meta={"period": f"{start}–{end}"},
                    )
                )
        return results

    @staticmethod
    def _in_range(mmdd: str, start: str, end: str) -> bool:
        """Попадание MM-DD в диапазон с учётом перехода через год.

        Лексикографическое сравнение работает корректно для формата 'MM-DD'.
        """
        if start <= end:
            return start <= mmdd <= end
        # обёрнутый диапазон, напр. 12-23..01-01
        return mmdd >= start or mmdd <= end
