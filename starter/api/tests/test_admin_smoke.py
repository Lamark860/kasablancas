"""Smoke-тест: /admin отвечает и видит каждую модель.

Использует реальный app с реальной БД (sqlite-файл из docker-compose), потому
что sqladmin привязан к engine на старте. Цель — убедиться, что подключение
sqladmin не сломано и каждая ModelView доступна.
"""
from fastapi.testclient import TestClient

from vlad.main import app


client = TestClient(app)


def test_admin_root_responds():
    r = client.get("/admin/")
    assert r.status_code == 200


def test_admin_lists_each_model():
    # sqladmin создаёт URL вида /admin/<identity>/list
    for identity in ("person", "plant", "oracle", "oracle-entry", "recommendation", "natal-chart"):
        r = client.get(f"/admin/{identity}/list")
        assert r.status_code == 200, f"{identity} -> {r.status_code}"


def test_api_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"name": "vlad-api", "version": "0.1.0"}


def test_ping():
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
