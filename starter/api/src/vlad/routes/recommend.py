"""POST /recommend — главный эндпоинт подбора растений.

Принимает либо person_id (для уже сохранённого клиента), либо inline-объект
person (одноразовый расчёт без записи в БД — удобно для проверок и публичного
бота на этапе 10). В обоих случаях возвращает пул кандидатов с источниками.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from vlad.core.orchestrator import recommend as run_orchestrator
from vlad.db import get_db
from vlad.models import Person
from vlad.schemas.recommendation import RecommendInput, RecommendOutput

router = APIRouter()


@router.post("/", response_model=RecommendOutput)
def recommend(
    payload: RecommendInput,
    apply_filters: bool = True,
    disabled: str | None = None,
    db: Session = Depends(get_db),
):
    """Главный эндпоинт. По умолчанию пул фильтруется (USDA, sun, soil,
    дерево-враг, is_weed_like). `?apply_filters=false` — эксперт смотрит «сырой»
    пул со всем, что выпало по символическим системам.

    `?disabled=oracle_a,oracle_b` — временно выключить оракулы в UI
    (fontes-тогглы), не трогая Oracle.active в БД. Удобно для исследования
    «а что если без славянского?».
    """
    if payload.person_id is not None:
        person = db.get(Person, payload.person_id)
        if person is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")
    else:
        # эфемерный Person: не добавляем в сессию, оракулы обращаются только
        # к атрибутам объекта и читают из БД свои entries
        person = Person(**payload.person.model_dump(exclude_unset=False))

    disabled_oracles = {s.strip() for s in (disabled or "").split(",") if s.strip()}
    return run_orchestrator(
        person, db,
        apply_filters_flag=apply_filters,
        disabled_oracles=disabled_oracles,
    )
