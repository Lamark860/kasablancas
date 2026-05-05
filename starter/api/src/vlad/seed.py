"""Сидинг справочников из data/seed/*.json.

Запуск:
    docker compose exec api python -m vlad.seed              # безопасный upsert
    docker compose exec api python -m vlad.seed --prune-missing
                                                             # затирает то, чего нет в JSON

По умолчанию — **безопасный upsert**: записи в БД, которых нет в сидах,
сохраняются. Это нужно, чтобы ручные правки эксперта в /admin не терялись
при reseed (см. DECISIONS.md §3).

Флаг ``--prune-missing`` возвращает старое поведение «JSON — единственный
источник истины»: всё, что не описано в JSON, удаляется. Полезно при
миграциях или когда в JSON удалили ошибочную запись и хочется её вынести
из БД.

Сейчас обрабатывается:
    data/seed/oracles.json    -> таблица oracles
    data/seed/plants.json     -> таблица plants
    data/seed/druid-tree.json -> oracle_entries (oracle_id='druid_tree')
    data/seed/zodiac.json     -> oracle_entries (oracle_id='zodiac')
    data/seed/numerology.json -> oracle_entries (oracle_id='numerology')
    data/seed/eye-color.json  -> oracle_entries (oracle_id='eye_color')
    data/seed/name.json       -> oracle_entries (oracle_id='name')
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select

from vlad.db import SessionLocal
from vlad.models import Oracle, OracleEntry, Plant


SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


def seed_oracles(session) -> int:
    path = SEED_DIR / "oracles.json"
    if not path.exists():
        print(f"  - {path.name}: пропуск (файл отсутствует)")
        return 0
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        session.merge(Oracle(**row))
    print(f"  + oracles.json: {len(rows)} записей")
    return len(rows)


def seed_plants(session) -> int:
    path = SEED_DIR / "plants.json"
    if not path.exists():
        print(f"  - {path.name}: пропуск (файл отсутствует, ждёт этапа 2)")
        return 0
    rows = json.loads(path.read_text(encoding="utf-8"))
    existing_by_slug = {p.slug: p for p in session.scalars(select(Plant)).all()}
    n = 0
    for row in rows:
        slug = row["slug"]
        if slug in existing_by_slug:
            for k, v in row.items():
                setattr(existing_by_slug[slug], k, v)
        else:
            session.add(Plant(**row))
        n += 1
    print(f"  + plants.json: {n} записей")
    return n


def _entry_key(oracle_id: str, matcher: dict, plant_slug: str) -> str:
    """Стабильный составной ключ для upsert OracleEntry.

    Уникален в текущих данных: для каждого `(oracle_id, plant_slug, matcher)`
    в семенах не более одной записи. role/weight/reason_* — атрибуты, не часть ключа.
    """
    canon = json.dumps(matcher, sort_keys=True, ensure_ascii=False)
    return f"{oracle_id}::{plant_slug}::{canon}"


def seed_oracle_entries(session, prune_missing: bool = False) -> int:
    """Сиды соответствий: data/seed/<oracle_id>.json (формат массива entry-объектов).

    По умолчанию — upsert по составному ключу (oracle_id, plant_slug, matcher).
    Записи, добавленные руками через /admin (нет в JSON), **сохраняются**.

    При prune_missing=True — удаляются все записи этого оракула, которых нет
    в JSON (включая ручные правки). Используется для жёсткого приведения БД
    к состоянию JSON-сидов.
    """
    total = 0
    for path in sorted(SEED_DIR.glob("*.json")):
        if path.name in {"oracles.json", "plants.json"}:
            continue
        oracle_id = path.stem.replace("-", "_")
        rows = json.loads(path.read_text(encoding="utf-8"))

        existing = list(session.query(OracleEntry).filter_by(oracle_id=oracle_id).all())
        existing_by_key = {
            _entry_key(oracle_id, e.matcher, e.plant_slug): e for e in existing
        }
        seed_keys: set[str] = set()
        added = updated = 0

        for row in rows:
            key = _entry_key(oracle_id, row["matcher"], row["plant_slug"])
            seed_keys.add(key)
            if key in existing_by_key:
                target = existing_by_key[key]
                for k, v in row.items():
                    setattr(target, k, v)
                updated += 1
            else:
                session.add(OracleEntry(oracle_id=oracle_id, **row))
                added += 1

        removed = 0
        if prune_missing:
            for key, target in existing_by_key.items():
                if key not in seed_keys:
                    session.delete(target)
                    removed += 1

        manual_kept = sum(1 for k in existing_by_key if k not in seed_keys) - removed
        total += len(rows)

        bits = [f"добавлено {added}", f"обновлено {updated}"]
        if prune_missing:
            bits.append(f"удалено {removed}")
        elif manual_kept:
            bits.append(f"ручных сохранено {manual_kept}")
        print(f"  + {path.name}: {oracle_id!r} — " + ", ".join(bits))
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vlad.seed", description="Сидинг справочников Vlad rev1.")
    parser.add_argument(
        "--prune-missing",
        action="store_true",
        help="Удалять записи oracle_entries, которых нет в JSON (включая ручные правки).",
    )
    args = parser.parse_args(argv)

    print("seed: старт" + (" (prune-missing)" if args.prune_missing else ""))
    if not SEED_DIR.exists():
        print(f"seed: каталог {SEED_DIR} не найден", file=sys.stderr)
        return 1

    with SessionLocal() as session:
        seed_oracles(session)
        seed_plants(session)
        seed_oracle_entries(session, prune_missing=args.prune_missing)
        session.commit()

    print("seed: готово")
    return 0


if __name__ == "__main__":
    sys.exit(main())
