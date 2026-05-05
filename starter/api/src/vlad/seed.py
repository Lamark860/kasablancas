"""Сидинг справочников из data/seed/*.json.

Запуск:
    docker compose exec api python -m vlad.seed

По умолчанию идемпотентно сливает каждый JSON в свою таблицу через session.merge —
строки с тем же PK обновляются, новые добавляются. Сами Person/Recommendation
остаются нетронутыми.

Сейчас обрабатывается:
    data/seed/oracles.json    -> таблица oracles
    data/seed/plants.json     -> таблица plants            (этап 2)
    data/seed/druid-tree.json -> oracle_entries (oracle_id='druid_tree') (этап 2)
    ...                         (далее по другим оракулам)
"""
from __future__ import annotations

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
    # merge по slug нельзя — slug не PK. Делаем upsert вручную.
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


def seed_oracle_entries(session) -> int:
    """Сиды соответствий: data/seed/<oracle_id>.json (формат массива entry-объектов).

    Каждый файл — полная замена записей этого оракула: сначала удаляем старые,
    затем вставляем новые. Это даёт право переписывать JSON без боли (см. roadmap).
    """
    total = 0
    for path in sorted(SEED_DIR.glob("*.json")):
        # пропускаем известные «не-entries» сиды
        if path.name in {"oracles.json", "plants.json"}:
            continue
        oracle_id = path.stem.replace("-", "_")
        rows = json.loads(path.read_text(encoding="utf-8"))
        # очистка старых
        session.query(OracleEntry).filter_by(oracle_id=oracle_id).delete()
        for row in rows:
            session.add(OracleEntry(oracle_id=oracle_id, **row))
        total += len(rows)
        print(f"  + {path.name}: {len(rows)} соответствий для {oracle_id!r}")
    return total


def main() -> int:
    print("seed: старт")
    if not SEED_DIR.exists():
        print(f"seed: каталог {SEED_DIR} не найден", file=sys.stderr)
        return 1

    with SessionLocal() as session:
        seed_oracles(session)
        seed_plants(session)
        seed_oracle_entries(session)
        session.commit()

    print("seed: готово")
    return 0


if __name__ == "__main__":
    sys.exit(main())
