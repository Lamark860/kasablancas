"""Тесты эндпоинта /geocode (F1: blur-валидация места рождения).

Реальный Nominatim не дёргаем (медленно, не воспроизводимо). Подмешиваем
search_places через monkeypatch.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from vlad.main import app
from vlad.natal.geocode import GeoResult


client = TestClient(app)


def test_geocode_returns_candidates(monkeypatch):
    fake = [
        GeoResult(lat=55.626, lon=37.606, tz="Europe/Moscow", label="Москва, Россия"),
    ]
    monkeypatch.setattr("vlad.routes.geocode.search_places", lambda q, limit=5: fake)
    r = client.get("/geocode/?q=Москва")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["lat"] == 55.626
    assert body[0]["tz"] == "Europe/Moscow"
    assert body[0]["label"] == "Москва, Россия"


def test_geocode_returns_empty_for_typo(monkeypatch):
    monkeypatch.setattr("vlad.routes.geocode.search_places", lambda q, limit=5: [])
    r = client.get("/geocode/?q=Мосвка")
    assert r.status_code == 200
    assert r.json() == []


def test_geocode_returns_multiple_for_ambiguous(monkeypatch):
    fake = [
        GeoResult(lat=51.5, lon=46.0, tz="Europe/Saratov", label="Александровск, Саратовская обл., Россия"),
        GeoResult(lat=59.1, lon=57.5, tz="Asia/Yekaterinburg", label="Александровск, Пермский край, Россия"),
    ]
    monkeypatch.setattr("vlad.routes.geocode.search_places", lambda q, limit=5: fake)
    r = client.get("/geocode/?q=Александровск")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["tz"] != body[1]["tz"]


def test_geocode_rejects_empty_q():
    r = client.get("/geocode/?q=")
    assert r.status_code == 422  # min_length=1


def test_geocode_respects_limit_cap():
    """limit > 10 → 422 (защита от перебора Nominatim)."""
    r = client.get("/geocode/?q=test&limit=99")
    assert r.status_code == 422


def test_search_places_handles_empty_input():
    """Без сети: пустая строка не уходит в Nominatim."""
    from vlad.natal.geocode import search_places
    assert search_places("") == []
    assert search_places("   ") == []


def test_search_places_returns_empty_when_geopy_missing(monkeypatch):
    """Если geopy не установлен (или импорт упал) — пустой список, не падаем."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "geopy.geocoders":
            raise ImportError("geopy not installed (test)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from vlad.natal.geocode import search_places
    assert search_places("Москва") == []
