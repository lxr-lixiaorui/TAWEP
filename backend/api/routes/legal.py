from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/agreements", response_class=HTMLResponse)
async def agreements() -> str:
    return "<h1>TAWEP Agreements</h1><p>Terms, privacy, and acceptable use rules for TAWEP.</p>"


@router.get("/credit-explanation", response_class=HTMLResponse)
async def credit_explanation() -> str:
    return "<h1>Credit Explanation</h1><p>Each evaluation costs 3 credits. Accounts start with 180 credits and can spend up to 60 credits every 7 days.</p>"
