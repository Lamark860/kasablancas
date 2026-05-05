"""PDF-рендер клиентского отчёта через Jinja2 + WeasyPrint."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from vlad.models import Person, Plant, Recommendation


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass
class _PoolItem:
    slug: str
    name_ru: str
    name_lat: str | None
    short_story: str | None
    expert_note: str | None = None


def _normalize_curated(curated_raw: list) -> list[dict]:
    """Старые записи: list[str]. Новые: list[{plant_slug, expert_note}]."""
    out: list[dict] = []
    for item in curated_raw:
        if isinstance(item, str):
            out.append({"plant_slug": item, "expert_note": None})
        elif isinstance(item, dict):
            out.append({
                "plant_slug": item["plant_slug"],
                "expert_note": item.get("expert_note"),
            })
    return out


def _resolve_curated(rec: Recommendation, db: Session) -> tuple[_PoolItem | None, list[_PoolItem]]:
    """Собрать главное дерево + сопровождающие, обогащённые из таблицы plants.

    Источник истины — `rec.raw_pool` (там уже есть plant_name_ru, short_story
    из оркестратора). `name_lat` подкачиваем из `Plant`. `expert_note` берём
    из curated_pool (заметка эксперта на конкретное растение, этап D9).
    """
    raw_by_slug = {p["plant_slug"]: p for p in (rec.raw_pool or [])}
    items = _normalize_curated(rec.curated_pool or [])
    title_slug = rec.title_plant_slug

    if title_slug and not any(it["plant_slug"] == title_slug for it in items):
        items.insert(0, {"plant_slug": title_slug, "expert_note": None})

    if not items:
        return None, []

    slugs = [it["plant_slug"] for it in items]
    plants_by_slug = {
        p.slug: p for p in db.query(Plant).filter(Plant.slug.in_(slugs)).all()
    }

    def make(item: dict) -> _PoolItem:
        slug = item["plant_slug"]
        raw = raw_by_slug.get(slug, {})
        plant = plants_by_slug.get(slug)
        return _PoolItem(
            slug=slug,
            name_ru=(raw.get("plant_name_ru") or (plant.name_ru if plant else slug)),
            name_lat=plant.name_lat if plant else None,
            short_story=raw.get("plant_short_story") or (plant.short_story if plant else None),
            expert_note=item.get("expert_note"),
        )

    main_slug = title_slug or items[0]["plant_slug"]
    main_item = next(it for it in items if it["plant_slug"] == main_slug)
    main = make(main_item)
    others = [make(it) for it in items if it["plant_slug"] != main_slug]
    return main, others


def render_client_report(person: Person, rec: Recommendation, db: Session) -> bytes:
    """Сгенерировать PDF клиентского отчёта. Возвращает байты PDF."""
    # импортируем weasyprint лениво — он медленный (~1с), не нужен в роутах
    # без PDF и в тестах, которые его не вызывают
    from weasyprint import HTML

    main, others = _resolve_curated(rec, db)
    template = _env.get_template("client_report.html")
    html = template.render(
        person=person,
        first_name=person.first_name,
        rec=rec,
        main=main,
        others=others,
        notes=rec.expert_notes,
    )
    return HTML(string=html).write_pdf()
