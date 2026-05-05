"""Дамп текущего состояния БД обратно в data/seed/*.json.

Кейс: коллега правит записи в /admin (новые соответствия, поправил weight,
добавил растение, ...) → запускает dump → JSON-файлы обновлены → можно
зафиксировать их в git как новый канон.

Запуск:
    docker compose exec api python -m vlad.dump_seed
    docker compose exec api python -m vlad.dump_seed --target-dir /tmp/seed-dump

Альтернатива через UI — кнопка в /admin (BaseView в admin.py).

Поведение:
    - Перезаписывает data/seed/plants.json, oracles.json,
      <oracle_id>.json (с дефисами вместо подчёркиваний — как в исходниках).
    - id у Plant и created_at/updated_at не выгружаются.
    - Поля со значением None опускаются (чтобы JSON был чище).
    - Файл для оракула не создаётся, если у него нет записей.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import SessionLocal
from vlad.models import Oracle, OracleEntry, Plant


SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


PLANT_FIELDS = [
    "slug", "name_ru", "name_lat", "aka", "category",
    "min_zone_usda", "max_zone_usda", "shelter_friendly",
    "height_max_m", "width_max_m", "growth_speed",
    "sun", "soil_moisture", "soil_type",
    "element", "gender_energy", "planet", "chakra",
    "bloom_months", "bloom_color", "autumn_color", "evergreen",
    "is_weed_like", "hierarchy_potential",
    "availability_ru", "approx_price_rub",
    "short_story", "long_story", "image_url",
]
ORACLE_FIELDS = ["id", "name_ru", "description", "active", "weight", "sort_order", "required_inputs"]
ENTRY_FIELDS = [
    "matcher", "plant_slug", "role", "weight",
    "reason_for_expert", "reason_for_client", "sort_order",
]


def _strip_nulls(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _write_json(path: Path, data: list) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dump_oracles(session: Session, target_dir: Path = SEED_DIR) -> int:
    rows = session.scalars(select(Oracle).order_by(Oracle.sort_order, Oracle.id)).all()
    data = [_strip_nulls({k: getattr(o, k) for k in ORACLE_FIELDS}) for o in rows]
    _write_json(target_dir / "oracles.json", data)
    return len(rows)


def dump_plants(session: Session, target_dir: Path = SEED_DIR) -> int:
    rows = session.scalars(select(Plant).order_by(Plant.slug)).all()
    data = [_strip_nulls({k: getattr(p, k) for k in PLANT_FIELDS}) for p in rows]
    _write_json(target_dir / "plants.json", data)
    return len(rows)


def dump_oracle_entries(session: Session, target_dir: Path = SEED_DIR) -> dict[str, int]:
    counts: dict[str, int] = {}
    oracle_ids = [o.id for o in session.scalars(select(Oracle).order_by(Oracle.id)).all()]
    for oid in oracle_ids:
        rows = (
            session.query(OracleEntry)
            .filter_by(oracle_id=oid)
            .order_by(OracleEntry.sort_order, OracleEntry.id)
            .all()
        )
        if not rows:
            continue
        data = [_strip_nulls({k: getattr(e, k) for k in ENTRY_FIELDS}) for e in rows]
        path = target_dir / f"{oid.replace('_', '-')}.json"
        _write_json(path, data)
        counts[oid] = len(rows)
    return counts


def dump_all(session: Session, target_dir: Path = SEED_DIR) -> dict[str, int]:
    """Главная точка входа. Возвращает {имя_файла: количество_записей}."""
    target_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, int] = {
        "plants.json": dump_plants(session, target_dir),
        "oracles.json": dump_oracles(session, target_dir),
    }
    for oid, n in dump_oracle_entries(session, target_dir).items():
        result[f"{oid.replace('_', '-')}.json"] = n
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vlad.dump_seed", description="Выгрузка справочников БД в data/seed/*.json.")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=SEED_DIR,
        help=f"Куда писать JSON. По умолчанию {SEED_DIR}.",
    )
    args = parser.parse_args(argv)

    print(f"dump_seed: старт, target_dir={args.target_dir}")
    with SessionLocal() as session:
        counts = dump_all(session, target_dir=args.target_dir)

    for name, n in counts.items():
        print(f"  + {name}: {n}")
    print("dump_seed: готово")
    return 0


if __name__ == "__main__":
    sys.exit(main())
