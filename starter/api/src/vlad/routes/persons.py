"""CRUD для Person (минимум, нужный для /recommend и UI эксперта)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import get_db
from vlad.models import Person
from vlad.natal.geocode import geocode_place
from vlad.schemas.person import PersonCreate, PersonOut

router = APIRouter()


@router.get("/", response_model=list[PersonOut])
def list_persons(db: Session = Depends(get_db)):
    return db.scalars(select(Person).order_by(Person.id.desc())).all()


@router.post("/", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=False)
    # best-effort геокодирование: если задано birth_place и lat/lon ещё пусты
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
