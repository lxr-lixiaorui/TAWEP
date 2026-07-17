from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas import CrossBorderConfigOut, LegalDocumentOut, LegalDocumentSummaryOut
from backend.services.legal_documents import get_document, list_documents
from backend.services.platform_settings import get_cross_border_config


router = APIRouter()


@router.get("/documents", response_model=list[LegalDocumentSummaryOut])
async def documents(
    locale: str = Query(default="en", pattern="^(en|zh)(?:-.+)?$"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    config = await get_cross_border_config(db)
    return list_documents(locale, cross_border_visible=config["visible"])


@router.get("/config", response_model=CrossBorderConfigOut)
async def legal_config(db: AsyncSession = Depends(get_db)) -> CrossBorderConfigOut:
    return CrossBorderConfigOut(**await get_cross_border_config(db))


@router.get("/documents/{slug}", response_model=LegalDocumentOut)
async def document(
    slug: str,
    locale: str = Query(default="en", pattern="^(en|zh)(?:-.+)?$"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if slug == "cross-border" and not (await get_cross_border_config(db))["visible"]:
        raise HTTPException(status_code=404, detail="Legal document not found")
    result = get_document(slug, locale)
    if result is None:
        raise HTTPException(status_code=404, detail="Legal document not found")
    return result
