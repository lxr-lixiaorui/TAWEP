from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.models import User
from backend.schemas import PublicReportOut, ReportShareOut
from backend.services.report_shares import create_report_share, get_public_report


router = APIRouter()


@router.post("/sessions/{session_id}/share", response_model=ReportShareOut, status_code=201)
async def share_report(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportShareOut:
    share = await create_report_share(db, user.id, session_id)
    if share is None:
        raise HTTPException(status_code=404, detail="Completed report not found")
    return share


@router.get("/shared-reports/{token}", response_model=PublicReportOut)
async def read_shared_report(
    token: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> PublicReportOut:
    shared_report = await get_public_report(db, token)
    if shared_report is None:
        raise HTTPException(status_code=404, detail="Shared report not found or no longer available")
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return shared_report
