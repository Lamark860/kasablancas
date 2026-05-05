"""Расчёт натальной карты через pyswisseph.

Решение по эфемеридам: используются встроенные **Moshier-эфемериды**
(`swe.FLG_MOSEPH`). Точность ~3 угловых секунды, с большим запасом для
назначения знаков зодиака. Внешние файлы `.se1` не нужны — это упрощает
docker-сборку и работу оффлайн. Если позже понадобится более точная
астрология (близкие аспекты, прогрессии) — положим файлы в `api/ephe/`
и переключим флаг.

Контракт и обоснования — в handoff/05-natal-chart.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe


SIGNS = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)

ELEMENT_BY_SIGN: dict[str, str] = {
    "aries": "fire", "leo": "fire", "sagittarius": "fire",
    "taurus": "earth", "virgo": "earth", "capricorn": "earth",
    "gemini": "air", "libra": "air", "aquarius": "air",
    "cancer": "water", "scorpio": "water", "pisces": "water",
}

PLANETS: list[tuple[str, int]] = [
    ("sun", swe.SUN),
    ("moon", swe.MOON),
    ("mercury", swe.MERCURY),
    ("venus", swe.VENUS),
    ("mars", swe.MARS),
    ("jupiter", swe.JUPITER),
    ("saturn", swe.SATURN),
    ("uranus", swe.URANUS),
    ("neptune", swe.NEPTUNE),
    ("pluto", swe.PLUTO),
]

_FLAGS = swe.FLG_MOSEPH


@dataclass
class ChartResult:
    sun_sign: str
    moon_sign: str
    ascendant_sign: str | None  # None если не задано время рождения / координаты

    planets: dict[str, dict[str, Any]]  # {'sun': {'sign': 'pisces', 'lon_deg': 344.5}, ...}

    fire_count: int
    earth_count: int
    air_count: int
    water_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def _sign_from_lon(lon_deg: float) -> str:
    return SIGNS[int(lon_deg % 360 // 30)]


def _to_utc(birth_date: date, birth_time: time | None, tz_name: str | None) -> datetime:
    """Сводит локальное рождение к UTC.

    Если времени или tz нет — берём 12:00 UTC. Это документированный компромисс:
    Солнце и медленные планеты от смещения внутри суток почти не зависят, а
    Луна на стыке знаков может ошибиться. UI должен предупреждать пользователя.
    """
    if birth_time and tz_name:
        local = datetime.combine(birth_date, birth_time, tzinfo=ZoneInfo(tz_name))
        return local.astimezone(ZoneInfo("UTC"))
    return datetime(
        birth_date.year, birth_date.month, birth_date.day,
        12, 0, tzinfo=ZoneInfo("UTC"),
    )


def calc_chart(
    birth_date: date,
    birth_time: time | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tz: str | None = None,
) -> ChartResult:
    utc = _to_utc(birth_date, birth_time, tz)
    jd = swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60 + utc.second / 3600,
    )

    planets: dict[str, dict[str, Any]] = {}
    counts = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    for name, code in PLANETS:
        positions, _flag = swe.calc_ut(jd, code, _FLAGS)
        lon_deg = positions[0]
        sign = _sign_from_lon(lon_deg)
        planets[name] = {"sign": sign, "lon_deg": round(lon_deg, 4)}
        counts[ELEMENT_BY_SIGN[sign]] += 1

    asc_sign: str | None = None
    if birth_time is not None and lat is not None and lon is not None:
        try:
            _cusps, ascmc = swe.houses(jd, lat, lon, b"P")  # Placidus
            asc_sign = _sign_from_lon(ascmc[0])
        except Exception:
            asc_sign = None

    return ChartResult(
        sun_sign=planets["sun"]["sign"],
        moon_sign=planets["moon"]["sign"],
        ascendant_sign=asc_sign,
        planets=planets,
        fire_count=counts["fire"],
        earth_count=counts["earth"],
        air_count=counts["air"],
        water_count=counts["water"],
    )


def parse_birth_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def parse_birth_time(s: str | None) -> time | None:
    if not s:
        return None
    try:
        h, m = s.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        return None
