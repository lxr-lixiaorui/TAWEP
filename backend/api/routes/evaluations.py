from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas import EvaluationJobOut
from backend.services.evaluation_jobs import get_evaluation_job, get_session_evaluation
from backend.services.example_data import EXAMPLE_SESSION_ID, build_example_evaluation_job


router = APIRouter()


@router.get("/{job_id}", response_model=EvaluationJobOut)
async def read_evaluation(job_id: UUID, db: AsyncSession = Depends(get_db)) -> EvaluationJobOut:
    if job_id == EXAMPLE_SESSION_ID:
        return build_example_evaluation_job()
    job = await get_evaluation_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return job


@router.get("/by-session/{session_id}", response_model=EvaluationJobOut)
async def read_session_evaluation(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EvaluationJobOut:
    if session_id == EXAMPLE_SESSION_ID:
        return build_example_evaluation_job()
    job = await get_session_evaluation(db, session_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return job
