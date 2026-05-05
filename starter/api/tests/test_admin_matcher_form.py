"""Тесты для кастомной формы OracleEntry.matcher в sqladmin.

Проверяем:
- _build_matcher собирает корректный dict для каждого из 5 типов
- create-страница рендерится 200 и содержит виртуальные поля
- create POST с правильными данными → 302 + запись с собранным matcher
- create POST без обязательного sub-поля → 400 (валидация)
- edit-страница prefill'ит виртуальные поля из существующего matcher
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from vlad.admin import _build_matcher
from vlad.db import SessionLocal
from vlad.main import app
from vlad.models import OracleEntry


client = TestClient(app)


def test_build_matcher_date_range():
    m = _build_matcher({"matcher_type": "date_range_yearly", "matcher_from": "03-05", "matcher_to": "04-01"})
    assert m == {"type": "date_range_yearly", "from": "03-05", "to": "04-01"}


def test_build_matcher_zodiac():
    m = _build_matcher({"matcher_type": "zodiac_sign", "matcher_sign": "taurus"})
    assert m == {"type": "zodiac_sign", "sign": "taurus"}


def test_build_matcher_numerology_int():
    m = _build_matcher({"matcher_type": "name_pythagorean_number", "matcher_number": "5"})
    assert m == {"type": "name_pythagorean_number", "number": 5}


def test_build_matcher_eye_color():
    m = _build_matcher({"matcher_type": "eye_color", "matcher_color": "blue"})
    assert m == {"type": "eye_color", "color": "blue"}


def test_build_matcher_name():
    m = _build_matcher({"matcher_type": "name_match", "matcher_name": "  Ева  "})
    assert m == {"type": "name_match", "name": "Ева"}


def test_build_matcher_unknown_returns_none():
    assert _build_matcher({"matcher_type": ""}) is None
    assert _build_matcher({"matcher_type": "garbage"}) is None


def test_create_form_renders_virtual_fields():
    r = client.get("/admin/oracle-entry/create")
    assert r.status_code == 200
    body = r.text
    for field in ("matcher_type", "matcher_from", "matcher_to",
                  "matcher_sign", "matcher_number", "matcher_color", "matcher_name",
                  "oracle_id", "plant_slug"):
        assert f'name="{field}"' in body, f"missing field: {field}"


def _cleanup_test_entries() -> None:
    with SessionLocal() as s:
        s.query(OracleEntry).filter(
            OracleEntry.reason_for_expert.like("PYTEST_A1%")
        ).delete()
        s.commit()


def test_create_post_date_range_persists_matcher():
    _cleanup_test_entries()
    r = client.post(
        "/admin/oracle-entry/create",
        data={
            "oracle_id": "druid_tree",
            "plant_slug": "birch",
            "weight": "1.0",
            "role": "main",
            "matcher_type": "date_range_yearly",
            "matcher_from": "05-25",
            "matcher_to": "06-03",
            "reason_for_expert": "PYTEST_A1 date_range",
            "reason_for_client": "test",
            "sort_order": "0",
            "save": "Save",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302
    with SessionLocal() as s:
        row = s.query(OracleEntry).filter_by(reason_for_expert="PYTEST_A1 date_range").one()
        assert row.matcher == {"type": "date_range_yearly", "from": "05-25", "to": "06-03"}
        assert row.oracle_id == "druid_tree"
        assert row.plant_slug == "birch"
    _cleanup_test_entries()


def test_create_post_zodiac_validation_fails_without_sign():
    _cleanup_test_entries()
    r = client.post(
        "/admin/oracle-entry/create",
        data={
            "oracle_id": "zodiac",
            "plant_slug": "oak",
            "weight": "1.0",
            "role": "main",
            "matcher_type": "zodiac_sign",
            "reason_for_expert": "PYTEST_A1 should fail",
            "save": "Save",
        },
        follow_redirects=False,
    )
    assert r.status_code == 400
    assert "Выберите знак" in r.text
    with SessionLocal() as s:
        assert s.query(OracleEntry).filter_by(reason_for_expert="PYTEST_A1 should fail").count() == 0


def test_edit_form_prefills_virtual_fields():
    _cleanup_test_entries()
    # создаём
    r = client.post(
        "/admin/oracle-entry/create",
        data={
            "oracle_id": "numerology",
            "plant_slug": "cedar",
            "weight": "0.7",
            "role": "companion",
            "matcher_type": "name_pythagorean_number",
            "matcher_number": "7",
            "reason_for_expert": "PYTEST_A1 prefill",
            "save": "Save",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302
    with SessionLocal() as s:
        new_id = s.query(OracleEntry).filter_by(reason_for_expert="PYTEST_A1 prefill").one().id

    r = client.get(f"/admin/oracle-entry/edit/{new_id}")
    assert r.status_code == 200
    body = r.text
    # matcher_type селектор должен иметь selected на name_pythagorean_number
    assert 'selected value="name_pythagorean_number"' in body or 'value="name_pythagorean_number" selected' in body
    # matcher_number должен иметь value="7"
    assert 'name="matcher_number"' in body and 'value="7"' in body
    _cleanup_test_entries()
