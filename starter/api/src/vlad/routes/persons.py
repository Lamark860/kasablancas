"""CRUD для Person + Recommendation (куратор-режим эксперта)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.core.orchestrator import recommend as run_orchestrator
from vlad.db import get_db
from vlad.models import Person, Recommendation
from vlad.natal.geocode import geocode_place
from vlad.schemas.curated import CuratedSave, RecommendationOut, RecommendationSummary
from vlad.schemas.person import PersonCreate, PersonOut

router = APIRouter()


@router.get("/", response_model=list[PersonOut])
def list_persons(db: Session = Depends(get_db)):
    return db.scalars(select(Person).order_by(Person.id.desc())).all()


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
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


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
    return rec


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
    return rows


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
    return rec
