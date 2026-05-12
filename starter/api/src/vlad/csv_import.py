"""Импорт oracle_entries из CSV.

CSV-колонки (header в первой строке, обязателен):
    oracle_id, plant_slug, matcher_type,
    matcher_from, matcher_to,        # date_range_yearly
    matcher_sign,                    # zodiac_sign
    matcher_number,                  # name_pythagorean_number
    matcher_color,                   # eye_color
    matcher_name,                    # name_match
    weight, role,
    reason_for_expert, reason_for_client,
    sort_order

Пустые ячейки → None. Для нерелевантных под matcher_type ячейки можно
оставлять пустыми, они не валидируются.

Используется как из CLI (для будущего), так и из админки через CsvImportView.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Iterable

from sqlalchemy.orm import Session

from vlad.matcher_describe import describe_matcher
from vlad.models import Oracle, OracleEntry, Plant
from vlad.seed import _entry_key


CSV_COLUMNS = [
    "oracle_id", "plant_slug", "matcher_type",
    "matcher_from", "matcher_to",
    "matcher_sign", "matcher_number",
    "matcher_color", "matcher_name",
    "weight", "role",
    "reason_for_expert", "reason_for_client",
    "sort_order",
]

MATCHER_TYPES = {
    "date_range_yearly", "zodiac_sign", "name_pythagorean_number",
    "eye_color", "name_match",
}
ZODIAC_SIGNS = {
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
}
EYE_COLORS = {"blue", "grey", "green", "hazel", "brown", "dark", "amber"}

_MMDD = re.compile(r"^\d{2}-\d{2}$")


# --- Парсинг строки CSV → matcher + поля entry --------------------------

def _strip(v: str | None) -> str:
    return (v or "").strip()


def _build_matcher(row: dict) -> dict | None:
    mt = _strip(row.get("matcher_type"))
    if mt == "date_range_yearly":
        return {"type": mt, "from": _strip(row.get("matcher_from")), "to": _strip(row.get("matcher_to"))}
    if mt == "zodiac_sign":
        return {"type": mt, "sign": _strip(row.get("matcher_sign")).lower()}
    if mt == "name_pythagorean_number":
        n_raw = _strip(row.get("matcher_number"))
        return {"type": mt, "number": int(n_raw) if n_raw.isdigit() else None}
    if mt == "eye_color":
        return {"type": mt, "color": _strip(row.get("matcher_color")).lower()}
    if mt == "name_match":
        return {"type": mt, "name": _strip(row.get("matcher_name"))}
    return None


def _validate_row(row: dict, valid_oracles: set[str], valid_plants: set[str]) -> tuple[dict | None, list[str]]:
    errors: list[str] = []

    oracle_id = _strip(row.get("oracle_id"))
    plant_slug = _strip(row.get("plant_slug"))
    mt = _strip(row.get("matcher_type"))

    if not oracle_id:
        errors.append("oracle_id пустой")
    elif oracle_id not in valid_oracles:
        errors.append(f"oracle_id '{oracle_id}' не существует в БД")
    if not plant_slug:
        errors.append("plant_slug пустой")
    elif plant_slug not in valid_plants:
        errors.append(f"plant_slug '{plant_slug}' не существует в БД")

    if not mt:
        errors.append("matcher_type пустой")
    elif mt not in MATCHER_TYPES:
        errors.append(f"matcher_type '{mt}' неизвестен (ожидается: {', '.join(sorted(MATCHER_TYPES))})")

    matcher = _build_matcher(row) if not errors else None

    if matcher is not None:
        if mt == "date_range_yearly":
            if not _MMDD.match(matcher["from"] or ""):
                errors.append(f"matcher_from '{matcher['from']}' не в формате MM-DD")
            if not _MMDD.match(matcher["to"] or ""):
                errors.append(f"matcher_to '{matcher['to']}' не в формате MM-DD")
        elif mt == "zodiac_sign":
            if matcher["sign"] not in ZODIAC_SIGNS:
                errors.append(f"matcher_sign '{matcher['sign']}' не из 12 знаков")
        elif mt == "name_pythagorean_number":
            n = matcher.get("number")
            if not isinstance(n, int) or not (1 <= n <= 9):
                errors.append(f"matcher_number должно быть 1..9, получено '{row.get('matcher_number')}'")
        elif mt == "eye_color":
            if matcher["color"] not in EYE_COLORS:
                errors.append(f"matcher_color '{matcher['color']}' не из {', '.join(sorted(EYE_COLORS))}")
        elif mt == "name_match":
            if not matcher["name"]:
                errors.append("matcher_name пустой")

    if errors:
        return None, errors

    # weight, sort_order
    try:
        weight = float(_strip(row.get("weight")) or "1.0")
    except ValueError:
        return None, [f"weight '{row.get('weight')}' не число"]
    try:
        sort_order = int(_strip(row.get("sort_order")) or "0")
    except ValueError:
        return None, [f"sort_order '{row.get('sort_order')}' не целое"]

    parsed = {
        "oracle_id": oracle_id,
        "plant_slug": plant_slug,
        "matcher": matcher,
        "weight": weight,
        # Пустые ячейки → None, чтобы noop-сравнение с существующими записями
        # (где role/reason_*/sort_order часто NULL) работало корректно.
        "role": _strip(row.get("role")) or None,
        "reason_for_expert": _strip(row.get("reason_for_expert")) or None,
        "reason_for_client": _strip(row.get("reason_for_client")) or None,
        "sort_order": sort_order,
    }
    return parsed, []


# --- Diff против БД ------------------------------------------------------

@dataclass
class RowDiff:
    line: int
    status: str   # "new" | "update" | "noop" | "error"
    parsed: dict | None
    existing_id: int | None
    errors: list[str] = field(default_factory=list)
    descr: str = ""


def preview(session: Session, csv_text: str) -> tuple[list[RowDiff], dict[str, int]]:
    """Распарсить CSV и сопоставить с БД. Не пишет ничего.

    Возвращает (rows, counts) — список row-дифов и сводку по статусам.
    """
    valid_oracles = {o.id for o in session.query(Oracle).all()}
    valid_plants = {p.slug for p in session.query(Plant).all()}

    rows: list[RowDiff] = []
    reader = csv.DictReader(io.StringIO(csv_text))
    for i, raw in enumerate(reader, start=2):  # line=1 — header
        parsed, errors = _validate_row(raw, valid_oracles, valid_plants)
        if errors:
            rows.append(RowDiff(line=i, status="error", parsed=None, existing_id=None, errors=errors))
            continue

        assert parsed is not None
        key = _entry_key(parsed["oracle_id"], parsed["matcher"], parsed["plant_slug"])
        existing = None
        for e in session.query(OracleEntry).filter_by(
            oracle_id=parsed["oracle_id"], plant_slug=parsed["plant_slug"]
        ).all():
            if _entry_key(e.oracle_id, e.matcher, e.plant_slug) == key:
                existing = e
                break

        descr = f"{parsed['oracle_id']} → {parsed['plant_slug']}: {describe_matcher(parsed['matcher'])}"
        if existing is None:
            rows.append(RowDiff(line=i, status="new", parsed=parsed, existing_id=None, descr=descr))
            continue

        # Сверяем атрибутивные поля
        changed = any(
            getattr(existing, k) != parsed[k]
            for k in ("weight", "role", "reason_for_expert", "reason_for_client", "sort_order")
        )
        status = "update" if changed else "noop"
        rows.append(RowDiff(line=i, status=status, parsed=parsed, existing_id=existing.id, descr=descr))

    counts = {"new": 0, "update": 0, "noop": 0, "error": 0}
    for r in rows:
        counts[r.status] += 1
    return rows, counts


def commit(session: Session, rows: list[RowDiff]) -> dict[str, int]:
    """Применить уже спрогнозированные изменения. Ошибочные строки пропускаются."""
    counts = {"created": 0, "updated": 0, "skipped": 0}
    for r in rows:
        if r.status == "error":
            counts["skipped"] += 1
            continue
        if r.status == "noop":
            counts["skipped"] += 1
            continue
        assert r.parsed is not None
        if r.status == "new":
            session.add(OracleEntry(**r.parsed))
            counts["created"] += 1
        elif r.status == "update":
            existing = session.get(OracleEntry, r.existing_id)
            if existing is None:
                # запись пропала за время preview → создаём
                session.add(OracleEntry(**r.parsed))
                counts["created"] += 1
                continue
            for k, v in r.parsed.items():
                setattr(existing, k, v)
            counts["updated"] += 1
    session.commit()
    return counts


# --- Template CSV (скачать пример) ---------------------------------------

def template_csv(oracle_id: str | None = None) -> str:
    """Вернуть CSV-шаблон с заголовком и 2 строками-примером.

    Если oracle_id указан и известен — пример настроен под этот тип матчера.
    """
    examples_by_oracle: dict[str, list[dict]] = {
        "druid_tree": [
            {"oracle_id": "druid_tree", "plant_slug": "willow", "matcher_type": "date_range_yearly",
             "matcher_from": "03-01", "matcher_to": "03-10", "weight": "1.0", "role": "main",
             "reason_for_expert": "Период ивы по друидам"},
            {"oracle_id": "druid_tree", "plant_slug": "oak", "matcher_type": "date_range_yearly",
             "matcher_from": "03-21", "matcher_to": "03-21", "weight": "1.0", "role": "main",
             "reason_for_expert": "Одиночный день дуба"},
        ],
        "zodiac": [
            {"oracle_id": "zodiac", "plant_slug": "oak", "matcher_type": "zodiac_sign",
             "matcher_sign": "leo", "weight": "1.0", "role": "main",
             "reason_for_expert": "Зодиак Лев — дуб"},
        ],
        "numerology": [
            {"oracle_id": "numerology", "plant_slug": "pine", "matcher_type": "name_pythagorean_number",
             "matcher_number": "4", "weight": "0.4", "role": "companion",
             "reason_for_expert": "Стабильность"},
        ],
        "eye_color": [
            {"oracle_id": "eye_color", "plant_slug": "oak", "matcher_type": "eye_color",
             "matcher_color": "brown", "weight": "0.6", "role": "companion",
             "reason_for_expert": "Карие глаза — земля"},
        ],
        "name": [
            {"oracle_id": "name", "plant_slug": "oak", "matcher_type": "name_match",
             "matcher_name": "Дарья", "weight": "1.0", "role": "main"},
        ],
    }

    if oracle_id and oracle_id in examples_by_oracle:
        rows = examples_by_oracle[oracle_id]
    else:
        # Универсальный набор: по одной строке каждого типа
        rows = [examples_by_oracle[k][0] for k in ("druid_tree", "zodiac", "numerology", "eye_color", "name")]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue()
