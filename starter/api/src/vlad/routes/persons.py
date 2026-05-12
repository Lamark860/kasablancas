"""CRUD для Person + Recommendation (куратор-режим эксперта)."""
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.core.orchestrator import recommend as run_orchestrator
from vlad.db import get_db
from vlad.models import Person, Plant, Recommendation
from vlad.natal.geocode import geocode_place
from vlad.schemas.curated import CuratedSave, RecommendationOut, RecommendationSummary
from vlad.schemas.person import PersonCreate, PersonOut

router = APIRouter()


def _plant_names_for_slugs(slugs: set[str], db: Session) -> dict[str, tuple[str, str | None]]:
    """Батч-фетч: slug → (name_ru, short_story). Пустой dict если slugs пусто."""
    if not slugs:
        return {}
    plants = db.scalars(select(Plant).where(Plant.slug.in_(slugs))).all()
    return {p.slug: (p.name_ru, p.short_story) for p in plants}


def _enrich_rec_out(rec: Recommendation, db: Session) -> RecommendationOut:
    """Заполняем title_plant_name_ru + plant_name_ru/short_story в curated_pool.

    Это нужно когда главное дерево или элемент curated отсутствуют в
    текущем raw_pool (оракулы/фильтры поменялись после кураторского выбора).
    """
    out = RecommendationOut.model_validate(rec)
    slugs: set[str] = set()
    if out.title_plant_slug:
        slugs.add(out.title_plant_slug)
    for it in (out.curated_pool or []):
        slugs.add(it.plant_slug)
    info = _plant_names_for_slugs(slugs, db)
    if out.title_plant_slug and out.title_plant_slug in info:
        out.title_plant_name_ru = info[out.title_plant_slug][0]
    for it in (out.curated_pool or []):
        if it.plant_slug in info:
            name_ru, story = info[it.plant_slug]
            it.plant_name_ru = name_ru
            it.plant_short_story = story
    return out


def _enrich_rec_summary(rows: list[Recommendation], db: Session) -> list[RecommendationSummary]:
    """То же для списка summary (история кураторских версий)."""
    slugs = {r.title_plant_slug for r in rows if r.title_plant_slug}
    for r in rows:
        for it in (r.curated_pool or []):
            if isinstance(it, dict) and it.get("plant_slug"):
                slugs.add(it["plant_slug"])
    info = _plant_names_for_slugs(slugs, db)
    out: list[RecommendationSummary] = []
    for r in rows:
        s = RecommendationSummary.model_validate(r)
        if s.title_plant_slug and s.title_plant_slug in info:
            s.title_plant_name_ru = info[s.title_plant_slug][0]
        for it in (s.curated_pool or []):
            if it.plant_slug in info:
                name_ru, story = info[it.plant_slug]
                it.plant_name_ru = name_ru
                it.plant_short_story = story
        out.append(s)
    return out


@router.get("/", response_model=list[PersonOut])
def list_persons(db: Session = Depends(get_db)):
    """Реестр гостий с производными полями для UI: status, last_touch_at,
    has_share_token. Сортировка — по last_touch_at (новейшая активность сверху).
    """
    persons = db.scalars(select(Person)).all()

    # Подтянем последние рекомендации одним запросом
    latest_by_person: dict[int, Recommendation] = {}
    for rec in db.scalars(
        select(Recommendation).order_by(Recommendation.id.desc())
    ).all():
        if rec.person_id not in latest_by_person:
            latest_by_person[rec.person_id] = rec

    enriched = []
    for p in persons:
        latest = latest_by_person.get(p.id)
        if latest is None:
            status_val = "intake"
            last_touch = p.updated_at
            has_token = False
        else:
            has_curated = bool(latest.curated_pool)
            status_val = "leaf" if has_curated else "pool"
            last_touch = max(p.updated_at, latest.created_at)
            has_token = bool(latest.share_token)

        # PersonOut собирается через from_attributes — но extra-полей в ORM
        # нет. Передаём словарь напрямую.
        out = PersonOut.model_validate(p).model_copy(update={
            "status": status_val,
            "last_touch_at": last_touch,
            "has_share_token": has_token,
        })
        enriched.append(out)

    # Новейшая активность сверху
    enriched.sort(key=lambda x: x.last_touch_at or x.created_at, reverse=True)
    return enriched


@router.post("/", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=False)
    if data.get("birth_place") and data.get("birth_lat") is None and data.get("birth_lon") is None:
        geo = geocode_place(data["birth_place"])
        if geo is not None:
            data["birth_lat"] = geo.lat
            data["birth_lon"] = geo.lon
            if data.get("birth_tz") is None:
                data["birth_tz"] = geo.tz
    person = Person(**data)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/{person_id}", response_model=PersonOut)
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(person_id: int, db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")
    db.delete(person)
    db.commit()


# ── куратор-режим: история Recommendation на person (D8) ──

def _latest_recommendation(db: Session, person_id: int) -> Recommendation | None:
    return db.scalars(
        select(Recommendation)
        .where(Recommendation.person_id == person_id)
        .order_by(Recommendation.id.desc())
        .limit(1)
    ).first()


@router.put("/{person_id}/recommendation", response_model=RecommendationOut)
def save_recommendation(
    person_id: int,
    payload: CuratedSave,
    db: Session = Depends(get_db),
):
    """Сохранить новую кураторскую версию для гостьи (D8 — каждый PUT плодит строку).

    Пересчитываем оркестратор с актуальными данными Person — это снимок,
    который потом рисуется в клиентский лист и в PDF. Старые версии
    остаются в БД, к ним можно вернуться через `GET /recommendations`.
    """
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")

    fresh = run_orchestrator(person, db, apply_filters_flag=payload.apply_filters)

    rec = Recommendation(
        person_id=person_id,
        input_snapshot={
            "first_name": person.first_name,
            "last_name": person.last_name,
            "birth_date": person.birth_date,
            "birth_time": person.birth_time,
            "birth_place": person.birth_place,
            "eye_color": person.eye_color,
            "garden_zone_usda": person.garden_zone_usda,
            "garden_sun": person.garden_sun,
            "garden_soil": person.garden_soil,
            "apply_filters": payload.apply_filters,
        },
        active_oracles=list(fresh["active_oracles"]),
        raw_pool=list(fresh["pool"]),
        # curated_pool храним в новом формате list[{plant_slug, expert_note}].
        # Старые записи в БД могут быть list[str] — нормализация на чтении.
        curated_pool=[item.model_dump() for item in (payload.curated or [])],
        title_plant_slug=payload.title_plant_slug,
        expert_notes=payload.expert_notes,
        # 16 байт url-safe → 22 символа (~128 бит энтропии). Стандарт для
        # неотзываемых публичных токенов: коллизия исчезающе мала, ссылка
        # короче и читабельнее в мессенджерах.
        share_token=secrets.token_urlsafe(16),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _enrich_rec_out(rec, db)




@router.get("/{person_id}/recommendation", response_model=RecommendationOut)
def get_recommendation(person_id: int, db: Session = Depends(get_db)):
    """Последняя сохранённая версия. Используется по умолчанию в `/client/{id}` и в PDF."""
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")
    rec = _latest_recommendation(db, person_id)
    if rec is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "recommendation not saved yet"
        )
    return _enrich_rec_out(rec, db)


@router.get(
    "/{person_id}/recommendations",
    response_model=list[RecommendationSummary],
)
def list_recommendations(person_id: int, db: Session = Depends(get_db)):
    """История кураторских версий для гостьи, новейшая первая (D8)."""
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")
    rows = db.scalars(
        select(Recommendation)
        .where(Recommendation.person_id == person_id)
        .order_by(Recommendation.id.desc())
    ).all()
    return _enrich_rec_summary(list(rows), db)


@router.get(
    "/{person_id}/recommendations/{rec_id}",
    response_model=RecommendationOut,
)
def get_recommendation_version(
    person_id: int,
    rec_id: int,
    db: Session = Depends(get_db),
):
    """Конкретная версия из истории."""
    rec = db.get(Recommendation, rec_id)
    if rec is None or rec.person_id != person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "recommendation version not found")
    return _enrich_rec_out(rec, db)


@router.post(
    "/{person_id}/recommendations/{rec_id}/finalize",
    response_model=RecommendationOut,
)
def finalize_recommendation_version(
    person_id: int,
    rec_id: int,
    db: Session = Depends(get_db),
):
    """Пометить эту версию как финальную, снять флаг с предыдущих.

    Идемпотентно: если уже финальная — просто возвращает её. Снимать
    финальность отдельным эндпоинтом не нужно: установка финальности на
    любой другой версии автоматически снимает её с этой.
    """
    rec = db.get(Recommendation, rec_id)
    if rec is None or rec.person_id != person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "recommendation version not found")
    # Снимаем со всех остальных
    others = db.scalars(
        select(Recommendation).where(
            Recommendation.person_id == person_id,
            Recommendation.id != rec_id,
            Recommendation.is_final.is_(True),
        )
    ).all()
    for o in others:
        o.is_final = False
    rec.is_final = True
    db.commit()
    db.refresh(rec)
    return _enrich_rec_out(rec, db)
