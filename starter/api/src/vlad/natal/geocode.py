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


def geocode_place(place: str) -> GeoResult | None:
    """Один сетевой запрос. Возвращает None при любой ошибке.

    Импорт geopy/timezonefinder лениво, чтобы не утаскивать сетевую
    зависимость в тесты, которые геокодинг не используют.
    """
    if not place or not place.strip():
        return None

    try:
        from geopy.geocoders import Nominatim
        from timezonefinder import TimezoneFinder
    except ImportError:
        logger.warning("geopy/timezonefinder не установлены — пропуск геокодирования")
        return None

    try:
        geocoder = Nominatim(user_agent="vlad-rev1")
        loc = geocoder.geocode(place, timeout=5)
    except Exception as e:
        logger.warning("геокодер не отвечает (%s): %s", type(e).__name__, e)
        return None

    if loc is None:
        return None

    try:
        tf = TimezoneFinder()
        tz = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
    except Exception as e:
        logger.warning("timezonefinder упал: %s", e)
        tz = None

    return GeoResult(lat=loc.latitude, lon=loc.longitude, tz=tz)
