"""Тесты CSV-импорта oracle_entries (vlad.csv_import + admin route /admin/csv-import)."""
from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from vlad import csv_import
from vlad.csv_import import CSV_COLUMNS
from vlad.main import app
from vlad.models import OracleEntry


client = TestClient(app)


def _make_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


# ────────────────────────── модуль ──────────────────────────

def test_template_csv_has_header_and_rows():
    txt = csv_import.template_csv("druid_tree")
    lines = txt.strip().split("\n")
    assert lines[0].startswith("oracle_id,plant_slug,matcher_type")
    assert any("willow" in l for l in lines[1:])


def test_preview_marks_unknown_oracle_as_error(seeded_session):
    csv_text = (
        "oracle_id,plant_slug,matcher_type,matcher_from,matcher_to,matcher_sign,matcher_number,matcher_color,matcher_name,weight,role,reason_for_expert,reason_for_client,sort_order\n"
        "unknown_oracle,willow,date_range_yearly,03-01,03-10,,,,,1.0,main,,,0\n"
    )
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts["error"] == 1
    assert counts["new"] == 0
    assert "unknown_oracle" in rows[0].errors[0]


def test_preview_marks_unknown_plant_as_error(seeded_session):
    csv_text = (
        "oracle_id,plant_slug,matcher_type,matcher_from,matcher_to,matcher_sign,matcher_number,matcher_color,matcher_name,weight,role,reason_for_expert,reason_for_client,sort_order\n"
        "druid_tree,no_such_plant,date_range_yearly,03-01,03-10,,,,,1.0,main,,,0\n"
    )
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts["error"] == 1
    assert "no_such_plant" in rows[0].errors[0]


def test_preview_marks_invalid_date_format(seeded_session):
    csv_text = (
        "oracle_id,plant_slug,matcher_type,matcher_from,matcher_to,matcher_sign,matcher_number,matcher_color,matcher_name,weight,role,reason_for_expert,reason_for_client,sort_order\n"
        "druid_tree,willow,date_range_yearly,march-1,03-10,,,,,1.0,main,,,0\n"
    )
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts["error"] == 1
    assert "MM-DD" in rows[0].errors[0]


def test_preview_detects_noop_for_existing_unchanged(seeded_session):
    # Берём существующую запись из сидов и составляем CSV-строку с теми же полями.
    existing = (
        seeded_session.query(OracleEntry)
        .filter_by(oracle_id="druid_tree", plant_slug="willow")
        .first()
    )
    assert existing is not None
    m = existing.matcher
    csv_text = _make_csv([{
        "oracle_id": "druid_tree",
        "plant_slug": "willow",
        "matcher_type": "date_range_yearly",
        "matcher_from": m["from"],
        "matcher_to": m["to"],
        "weight": existing.weight,
        "role": existing.role or "",
        "reason_for_expert": existing.reason_for_expert or "",
        "reason_for_client": existing.reason_for_client or "",
        "sort_order": existing.sort_order or 0,
    }])
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts["noop"] == 1
    assert counts["new"] == counts["update"] == counts["error"] == 0


def test_preview_detects_update_when_weight_changes(seeded_session):
    existing = (
        seeded_session.query(OracleEntry)
        .filter_by(oracle_id="druid_tree", plant_slug="willow")
        .first()
    )
    m = existing.matcher
    new_weight = (existing.weight or 1.0) + 0.5
    csv_text = (
        "oracle_id,plant_slug,matcher_type,matcher_from,matcher_to,matcher_sign,matcher_number,matcher_color,matcher_name,weight,role,reason_for_expert,reason_for_client,sort_order\n"
        f"druid_tree,willow,date_range_yearly,{m['from']},{m['to']},,,,,{new_weight},{existing.role or 'main'},,,0\n"
    )
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts["update"] == 1
    assert rows[0].existing_id == existing.id


def test_preview_new_for_zodiac_with_extra_sign(seeded_session):
    # Aries в seed-наборе zodiac.json пуст — добавим новую запись.
    csv_text = (
        "oracle_id,plant_slug,matcher_type,matcher_from,matcher_to,matcher_sign,matcher_number,matcher_color,matcher_name,weight,role,reason_for_expert,reason_for_client,sort_order\n"
        "zodiac,oak,zodiac_sign,,,aries,,,,1.0,main,Овен → дуб,,0\n"
    )
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts["new"] == 1
    assert rows[0].descr.startswith("zodiac")


def test_commit_creates_and_updates(seeded_session):
    existing = (
        seeded_session.query(OracleEntry)
        .filter_by(oracle_id="druid_tree", plant_slug="willow")
        .first()
    )
    m = existing.matcher
    new_weight = (existing.weight or 1.0) + 0.5
    before_count = seeded_session.query(OracleEntry).count()

    csv_text = (
        "oracle_id,plant_slug,matcher_type,matcher_from,matcher_to,matcher_sign,matcher_number,matcher_color,matcher_name,weight,role,reason_for_expert,reason_for_client,sort_order\n"
        # update existing
        f"druid_tree,willow,date_range_yearly,{m['from']},{m['to']},,,,,{new_weight},{existing.role or 'main'},,,0\n"
        # new zodiac entry
        "zodiac,oak,zodiac_sign,,,aries,,,,1.0,main,Овен → дуб,,0\n"
    )
    rows, counts = csv_import.preview(seeded_session, csv_text)
    assert counts == {"new": 1, "update": 1, "noop": 0, "error": 0}
    result = csv_import.commit(seeded_session, rows)
    assert result == {"created": 1, "updated": 1, "skipped": 0}

    after_count = seeded_session.query(OracleEntry).count()
    assert after_count == before_count + 1
    # И вес обновился
    updated = (
        seeded_session.query(OracleEntry)
        .filter_by(id=existing.id)
        .first()
    )
    assert updated.weight == new_weight


# ────────────────────────── HTTP-роут ──────────────────────────

def test_csv_import_page_get_renders():
    r = client.get("/admin/csv-import")
    assert r.status_code == 200
    assert "Импорт соответствий" in r.text


def test_csv_import_template_download():
    r = client.get("/admin/csv-import?template=druid_tree")
    assert r.status_code == 200
    assert "oracle_id" in r.text  # header
    assert "willow" in r.text
    assert r.headers.get("content-disposition", "").startswith("attachment")


def test_csv_import_preview_empty_returns_warning():
    r = client.post("/admin/csv-import", data={"action": "preview", "csv_text": ""})
    assert r.status_code == 200
    assert "Пустой CSV" in r.text
