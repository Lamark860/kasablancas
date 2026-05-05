"""GET /plants — справочник растений (для UI и автодополнения)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import get_db
from vlad.models import Plant

router = APIRouter()


class PlantBrief(BaseModel):
    id: int
    slug: str
    name_ru: str
    name_lat: str | None
    category: str
    min_zone_usda: int | None
    hierarchy_potential: int | None
    short_story: str | None

    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=list[PlantBrief])
def list_plants(db: Session = Depends(get_db)):
    return db.scalars(select(Plant).order_by(Plant.name_ru)).all()
