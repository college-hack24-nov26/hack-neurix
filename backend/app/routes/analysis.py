"""
HomeCare+ — AI Image & Report Analysis Routes
GET  /analysis/status    — which AI capabilities are configured (cheap, no API calls)
GET  /analysis/diagnose  — live test of every vision provider (auth required, sends a tiny image)
POST /analysis/image     — analyse an uploaded medical image / scan / skin photo
POST /analysis/report    — summarise a medical report (PDF, photo or text)
"""
import logging

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.middleware.auth import get_current_user
from app.services.analysis_service import AnalysisService, AnalysisError
from app.services.ai_service import AIService
from app.services.vision_providers import configured_providers, diagnose

logger = logging.getLogger(__name__)
router = APIRouter()
service = AnalysisService()

VALID_TYPES = {"xray", "scan", "skin", "report"}


async def _read_upload(file: UploadFile) -> bytes:
    """Read an upload with a hard size cap (never trusts Content-Type or Content-Length)."""
    limit = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    data = await file.read(limit + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB.")
    return data


def _error_response(e: AnalysisError) -> JSONResponse:
    return JSONResponse(
        status_code=e.status_code,
        content={"detail": e.message, "attempts": e.attempts},
    )


@router.get("/status")
async def ai_status():
    """Report which AI capabilities are usable so the UI can show an accurate message."""
    vision = configured_providers(vision=True)
    chat_ok = AIService.is_configured()
    vision_ok = bool(vision)
    return {
        "chat_available": chat_ok,
        "vision_available": vision_ok,
        "vision_providers": vision,
        "providers": {
            "openai": AIService.has_key("openai"),
            "anthropic": AIService.has_key("anthropic"),
            "groq": AIService.has_key("groq"),
        },
        "message": (
            "All AI features ready." if vision_ok else
            "Chat is ready, but image analysis needs an Anthropic, OpenAI or Groq key in backend/.env."
            if chat_ok else
            "No AI provider configured. Add an API key to backend/.env to enable real AI responses."
        ),
    }


@router.get("/diagnose")
async def ai_diagnose(current_user=Depends(get_current_user)):
    """Live connectivity test: sends a tiny generated image to every configured vision provider."""
    results = await diagnose()
    return {
        "ok": any(r["ok"] for r in results),
        "providers": results,
        "message": (
            "At least one vision provider is working." if any(r["ok"] for r in results)
            else "No vision provider answered successfully — see the reasons below."
            if results else "No vision provider has an API key configured."
        ),
    }


@router.post("/image")
async def analyze_image(
    file:         UploadFile = File(...),
    type:         str        = Form("xray"),
    language:     str        = Form("en"),
    current_user              = Depends(get_current_user),
):
    if type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail="Invalid analysis type.")
    data = await _read_upload(file)
    try:
        return await service.analyze_bytes(data, analysis_type=type, language=language)
    except AnalysisError as e:
        return _error_response(e)


@router.post("/report")
async def summarize_report(
    file:         UploadFile = File(...),
    language:     str        = Form("en"),
    current_user              = Depends(get_current_user),
):
    data = await _read_upload(file)
    try:
        return await service.summarize_bytes(data, language=language)
    except AnalysisError as e:
        return _error_response(e)
