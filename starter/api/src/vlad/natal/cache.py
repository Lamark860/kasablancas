"""Кеш натальной карты в таблице natal_charts.

Для сохранённого Person (есть id) — пробуем достать из БД, иначе считаем и
сохраняем. Для эфемерного Person (id=None, режим inline у /recommend) —
просто считаем без сохранения.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from vlad.models import NatalChart as NatalChartModel

from .swisseph_wrapper import (
    ChartResult,
    calc_chart,
    parse_birth_date,
    parse_birth_time,
)


def get_or_calc_chart(person, db: Session) -> ChartResult | None:
    """Возвращает карту или None, если у Person нет валидной даты рождения."""
    bd = parse_birth_date(getattr(person, "birth_date", None))
    if bd is None:
        return None

    person_id = getattr(person, "id", None)
    if person_id:
        cached = db.get(NatalChartModel, person_id)
        if cached is not None and cached.full_chart:
            return ChartResult(**cached.full_chart)

    chart = calc_chart(
        birth_date=bd,
        birth_time=parse_birth_time(getattr(person, "birth_time", None)),
        lat=getattr(person, "birth_lat", None),
        lon=getattr(person, "birth_lon", None),
        tz=getattr(person, "birth_tz", None),
    )

    if person_id:
        db.add(
            NatalChartModel(
                person_id=person_id,
                sun_sign=chart.sun_sign,
                moon_sign=chart.moon_sign,
                ascendant_sign=chart.ascendant_sign,
                fire_count=chart.fire_count,
                earth_count=chart.earth_count,
                air_count=chart.air_count,
                water_count=chart.water_count,
                full_chart=chart.to_dict(),
            )
        )
        db.commit()

    return chart
