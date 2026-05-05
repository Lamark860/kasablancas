"""Имя → растение.

Прямая таблица соответствий из research/06-name-plants.md (подход A —
этимология). Сравнение нечувствительно к регистру и склонениям не
учитывает (Анна и Анны — разные строки; нормализуем в самой записи matcher).

Намеренно расширяемая база: каждый новый клиент = повод добавить его имя
в `data/seed/name.json` с растением. Сейчас в сидах — только те имена, чьи
растения есть в plants.json.
"""
from __future__ import annotations

from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.models import OracleEntry

from .base import Oracle, OracleResult


class NameOracle(Oracle):
    id: ClassVar[str] = "name"
    name_ru: ClassVar[str] = "Имя → растение"
    required_inputs: ClassVar[list[str]] = ["first_name"]

    def run(self, person, db: Session) -> list[OracleResult]:
        if not self.can_run_for(person):
            return []
        name = (getattr(person, "first_name", "") or "").strip().lower()
        if not name:
            return []

        entries = db.scalars(
            select(OracleEntry).where(OracleEntry.oracle_id == self.id)
        ).all()
        results: list[OracleResult] = []
        for e in entries:
            m = e.matcher or {}
            if m.get("type") != "name_match":
                continue
            target = (m.get("name") or "").strip().lower()
            if not target:
                continue
            if target != name:
                continue
            results.append(
                OracleResult(
                    plant_slug=e.plant_slug,
                    weight=e.weight,
                    role=e.role,
                    reason_for_expert=e.reason_for_expert or "",
                    reason_for_client=e.reason_for_client or "",
                    meta={"name": target},
                )
            )
        return results
