"""PDF-отчёты для клиента."""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from vlad.db import get_db
from vlad.models import Person, Recommendation
from vlad.pdf import render_client_report

router = APIRouter()


@router.get("/{person_id}.pdf")
def client_report_pdf(person_id: int, db: Session = Depends(get_db)):
    """PDF-отчёт для клиента (без указания источников).

    Берётся последняя сохранённая Recommendation; если её ещё нет — 404,
    эксперт должен сначала зайти на /expert/{id} и нажать «сохранить».
    """
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "person not found")

    rec = db.scalars(
        select(Recommendation)
        .where(Recommendation.person_id == person_id)
        .order_by(Recommendation.id.desc())
        .limit(1)
    ).first()
    if rec is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "recommendation not saved yet — куратору сначала надо зайти на /expert и сохранить",
        )

    pdf_bytes = render_client_report(person, rec, db)
    # Имя гостьи может быть кириллицей — заголовок HTTP принимает только latin-1.
    # ASCII-fallback + RFC 5987 filename* для современных браузеров.
    filename = f"hortus-animae-{person.first_name}-{person_id}.pdf"
    ascii_fallback = f"hortus-animae-{person_id}.pdf"
    disposition = (
        f'inline; filename="{ascii_fallback}"; filename*=UTF-8\'\'{quote(filename)}'
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": disposition},
    )
