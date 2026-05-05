"""Геокодирование birth_place → (lat, lon, tz).

Использует Nominatim (OpenStreetMap, без ключа), как best-effort. Сбой
геокодера (нет сети, лимит, неизвестное место) не блокирует создание Person —
просто оставляет lat/lon/tz пустыми, эксперт может заполнить их вручную
через /admin.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GeoResult:
    lat: float
    lon: float
    tz: str | None
    label: str | None = None  # человекочитаемое имя из OSM (для disambiguation в UI)


def _resolve_tz(lat: float, lon: float) -> str | None:
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        return tf.timezone_at(lat=lat, lng=lon)
    except Exception as e:
        logger.warning("timezonefinder упал: %s", e)
        return None


def search_places(place: str, limit: int = 5) -> list[GeoResult]:
    """Поиск кандидатов для disambiguation (F1: место рождения).

    В отличие от `geocode_place`, возвращает СПИСОК — UI показывает
    его пользователю, если результатов больше одного. Пустой список
    означает «не найдено» (опечатка / неизвестное место / нет сети).
    """
    if not place or not place.strip():
        return []

    try:
        from geopy.geocoders import Nominatim
    except ImportError:
        logger.warning("geopy не установлен — пропуск геокодирования")
        return []

    try:
        geocoder = Nominatim(user_agent="vlad-rev1")
        # exactly_one=False даёт list[Location], limit ограничивает выдачу
        locs = geocoder.geocode(place, exactly_one=False, limit=limit, timeout=5)
    except Exception as e:
        logger.warning("геокодер не отвечает (%s): %s", type(e).__name__, e)
        return []

    if not locs:
        return []

    return [
        GeoResult(
            lat=loc.latitude,
            lon=loc.longitude,
            tz=_resolve_tz(loc.latitude, loc.longitude),
            label=getattr(loc, "address", None) or place,
        )
        for loc in locs
    ]


def geocode_place(place: str) -> GeoResult | None:
    """Один сетевой запрос, первый кандидат. Backward-compat для POST /persons.

    Возвращает None при любой ошибке. Используется когда фронт не
    передал явные lat/lon — best-effort на стороне бэка (см. DECISIONS §14).
    """
    candidates = search_places(place, limit=1)
    return candidates[0] if candidates else None
