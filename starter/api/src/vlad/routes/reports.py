from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()


@router.get("/{person_id}.pdf")
def client_report_pdf(person_id: int):
    """PDF-отчёт для клиента (без указания источников)."""
    # TODO: WeasyPrint -> bytes
    return Response(content=b"%PDF-stub", media_type="application/pdf")
