"""Цвет глаз → растение.

Авторская привязка из research/07-other-systems.md (раздел «Цвет глаз»).
Покрывает только те цвета, для которых в plants.json есть подходящие
растения. Для зелёных/янтарных/чёрных глаз пока сидов нет — растения
этих секторов (папоротник, плющ, золотарник, бузина) не входят в наши 22.
"""
from __future__ import annotations

from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.models import OracleEntry

from .base import Oracle, OracleResult


class EyeColorOracle(Oracle):
    id: ClassVar[str] = "eye_color"
    name_ru: ClassVar[str] = "Цвет глаз → стихия → растения"
    required_inputs: ClassVar[list[str]] = ["eye_color"]

    def run(self, person, db: Session) -> list[OracleResult]:
        if not self.can_run_for(person):
            return []
        color = getattr(person, "eye_color", None)
        if not color:
            return []

        entries = db.scalars(
            select(OracleEntry).where(OracleEntry.oracle_id == self.id)
        ).all()
        results: list[OracleResult] = []
        for e in entries:
            m = e.matcher or {}
            if m.get("type") != "eye_color":
                continue
            if m.get("color") != color:
                continue
            results.append(
                OracleResult(
                    plant_slug=e.plant_slug,
                    weight=e.weight,
                    role=e.role,
                    reason_for_expert=e.reason_for_expert or "",
                    reason_for_client=e.reason_for_client or "",
                    meta={"eye_color": color},
                )
            )
        return results
