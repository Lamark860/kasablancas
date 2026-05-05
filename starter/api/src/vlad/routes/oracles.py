"""GET /oracles — список оракулов с метаданными."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import get_db
from vlad.models import Oracle
from vlad.oracles import ORACLES

router = APIRouter()


class OracleBrief(BaseModel):
    id: str
    name_ru: str
    description: str | None
    active: int
    weight: float
    required_inputs: list
    sort_order: int
    implemented: bool   # есть ли класс-реализация в registry

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[OracleBrief])
def list_oracles(db: Session = Depends(get_db)):
    rows = db.scalars(select(Oracle).order_by(Oracle.sort_order)).all()
    return [
        OracleBrief(
            id=o.id,
            name_ru=o.name_ru,
            description=o.description,
            active=o.active,
            weight=o.weight,
            required_inputs=o.required_inputs,
            sort_order=o.sort_order,
            implemented=o.id in ORACLES,
        )
        for o in rows
    ]
