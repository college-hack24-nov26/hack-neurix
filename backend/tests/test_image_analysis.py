"""
Image / report analysis tests — no database, no real LLM calls.
Providers are faked with httpx.MockTransport.

    cd backend && pytest tests/test_image_analysis.py
"""
import asyncio
import io
import json

import httpx
import pytest
from PIL import Image

from app.config.settings import settings
from app.services import vision_providers as vp
from app.services.analysis_service import AnalysisError, AnalysisService
from app.services.image_utils import ImageError, prepare_image

FAKE = "k" * 40


def run(coro):
    return asyncio.run(coro)


def make_image(size=(900, 700), mode="RGB", fmt="PNG"):
    img = Image.effect_noise(size, 60).convert("L") if mode != "RGB" else Image.effect_noise(size, 60).convert("RGB")
    if mode not in ("RGB", "L"):
        img = img.convert(mode)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", FAKE)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", FAKE)
    monkeypatch.setattr(settings, "GROQ_API_KEY", FAKE)
    monkeypatch.setattr(settings, "VISION_PROVIDER_ORDER", "anthropic,openai,groq")   # independent of local .env
    monkeypatch.setattr(vp, "_transport", None)
    yield
    monkeypatch.setattr(vp, "_transport", None)


def use_transport(monkeypatch, handler):
    monkeypatch.setattr(vp, "_transport", httpx.MockTransport(handler))


GOOD = {
    "image_valid": True, "image_issue": "", "detected_type": "frontal chest X-ray",
    "image_quality": {"rating": "good", "issues": []},
    "summary": "Lungs look clear.", "key_findings": ["Clear lung fields — both lungs — normal"],
    "possible_conditions": [{"name": "No acute abnormality", "likelihood": "high", "reasoning": "clear"}],
    "urgency": "routine", "urgency_reason": "nothing concerning",
    "recommendations": ["Routine follow-up"], "questions_for_doctor": ["Is a repeat needed?"],
    "limitations": ["Single view"], "confidence": 97,
}


def anthropic_ok(body):
    return httpx.Response(200, json={"content": [{"type": "text", "text": json.dumps(body)}]})


# ── image preparation ─────────────────────────────────────────────────────────

def test_large_bmp_is_converted_and_resized():
    prepared = prepare_image(make_image((3000, 2400), fmt="BMP"))
    assert prepared.media_type == "image/jpeg"
    assert max(prepared.width, prepared.height) <= settings.VISION_MAX_EDGE
    assert prepared.resized and prepared.original_format == "BMP"
    assert len(prepared.b64) < 3_800_000


def test_16bit_grayscale_png_is_not_blown_out():
    img = Image.new("I;16", (600, 600))
    img.putdata([(x % 600) * 100 for x in range(600 * 600)])
    buf = io.BytesIO(); img.save(buf, format="PNG")
    prepared = prepare_image(buf.getvalue())
    assert prepared.width == 600


def test_rgba_png_flattened():
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    assert prepare_image(buf.getvalue()).media_type == "image/jpeg"


@pytest.mark.parametrize("data,msg", [
    (b"", "empty"),
    (b"%PDF-1.4 something", "PDF"),
    (b"\x00\x01\x02garbage" * 50, "Unsupported"),
])
def test_bad_uploads_rejected(data, msg):
    with pytest.raises(ImageError) as e:
        prepare_image(data)
    assert msg in str(e.value)


def test_tiny_image_rejected():
    with pytest.raises(ImageError):
        prepare_image(make_image((50, 50)))


# ── provider chain ────────────────────────────────────────────────────────────

def test_fallback_to_next_provider_when_first_key_rejected(monkeypatch):
    def handler(request):
        if "anthropic" in request.url.host:
            return httpx.Response(401, json={"error": {"message": "invalid x-api-key"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(GOOD)}}]})
    use_transport(monkeypatch, handler)
    result = run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert result["provider"] == "openai" and result["status"] == "ok"


def test_primary_model_missing_uses_fallback_model(monkeypatch):
    seen = []
    def handler(request):
        model = json.loads(request.content)["model"]
        seen.append(model)
        if model == settings.ANTHROPIC_VISION_MODEL:
            return httpx.Response(404, json={"error": {"message": "model not found"}})
        return anthropic_ok(GOOD)
    use_transport(monkeypatch, handler)
    result = run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert result["provider"] == "anthropic" and result["model"] == settings.ANTHROPIC_FALLBACK_MODEL
    assert len(seen) == 2


def test_all_providers_fail_gives_clear_error_not_fake_result(monkeypatch):
    use_transport(monkeypatch, lambda r: httpx.Response(401, json={"error": {"message": "nope"}}))
    with pytest.raises(AnalysisError) as e:
        run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert e.value.status_code == 503
    assert {a["provider"] for a in e.value.attempts} == {"anthropic", "openai", "groq"}
    assert FAKE not in e.value.message


def test_no_keys_configured(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"):
        monkeypatch.setattr(settings, k, "")
    with pytest.raises(AnalysisError) as e:
        run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert "No AI vision provider" in e.value.message


def test_placeholder_key_counts_as_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "your_openai_api_key_here")
    assert "openai" not in vp.configured_providers(vision=True)


# ── result normalisation ──────────────────────────────────────────────────────

def test_confidence_capped_by_image_quality(monkeypatch):
    bad = {**GOOD, "image_quality": {"rating": "poor", "issues": ["blurry"]}, "confidence": 95}
    use_transport(monkeypatch, lambda r: anthropic_ok(bad))
    result = run(AnalysisService().analyze_bytes(make_image(), "skin"))
    assert result["confidence"] == 35


def test_emergency_urgency_adds_action(monkeypatch):
    body = {**GOOD, "urgency": "emergency", "urgency_reason": "large pneumothorax"}
    use_transport(monkeypatch, lambda r: anthropic_ok(body))
    result = run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert result["urgency"] == "emergency"
    assert "112" in result["recommendations"][0]


def test_wrong_image_type_reported_as_unusable(monkeypatch):
    body = {"image_valid": False, "image_issue": "This is a photo of a dog, not an X-ray."}
    use_transport(monkeypatch, lambda r: anthropic_ok(body))
    result = run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert result["status"] == "unusable_image" and result["confidence"] == 0
    assert "dog" in result["summary"]


def test_prose_reply_is_wrapped_honestly(monkeypatch):
    use_transport(monkeypatch, lambda r: httpx.Response(200, json={"content": [{"type": "text", "text": "Looks fine to me."}]}))
    result = run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert result["confidence"] <= 30 and "Looks fine" in result["summary"]


def test_malformed_model_fields_do_not_crash(monkeypatch):
    weird = {"image_valid": True, "summary": "ok", "key_findings": "single string",
             "possible_conditions": ["Plain string condition"], "confidence": "85%",
             "urgency": "SOMETHING", "recommendations": None}
    use_transport(monkeypatch, lambda r: anthropic_ok(weird))
    result = run(AnalysisService().analyze_bytes(make_image(), "scan"))
    assert result["key_findings"] == ["single string"]
    assert result["possible_conditions"][0]["name"] == "Plain string condition"
    assert result["urgency"] == "soon" and isinstance(result["confidence"], int)


# ── reports ───────────────────────────────────────────────────────────────────

def test_text_report_summary(monkeypatch):
    rep = {"report_type": "CBC", "test_date": "2026-10-01", "lab_name": "Lab X", "summary": "Low Hb.",
           "findings": [{"parameter": "Hemoglobin", "value": "9.1 g/dL", "normal_range": "12-16", "status": "LOW", "note": "low"}],
           "recommendations": ["See doctor"]}
    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(rep)}}]}) \
            if "groq" in request.url.host else httpx.Response(500)
    use_transport(monkeypatch, handler)
    out = run(AnalysisService().summarize_bytes(b"Hemoglobin 9.1 g/dL (12-16) Complete blood count report text"))
    assert out["findings"][0]["status"] == "low" and out["provider"] == "groq"


def test_diagnose_reports_per_provider(monkeypatch):
    def handler(request):
        if "anthropic" in request.url.host:
            return httpx.Response(200, json={"content": [{"type": "text", "text": "OK"}]})
        return httpx.Response(401, json={"error": {"message": "bad key"}})
    use_transport(monkeypatch, handler)
    report = {r["provider"]: r for r in run(vp.diagnose())}
    assert report["anthropic"]["ok"] and not report["openai"]["ok"] and "rejected" in report["openai"]["reason"]


# ── HTTP layer (router only, auth stubbed) ────────────────────────────────────

def _client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.middleware.auth import get_current_user
    from app.routes import analysis
    app = FastAPI()
    app.include_router(analysis.router, prefix="/api/analysis")
    app.dependency_overrides[get_current_user] = lambda: {"id": "u1"}
    return TestClient(app)


def test_http_image_endpoint_ok_and_errors(monkeypatch):
    use_transport(monkeypatch, lambda r: anthropic_ok(GOOD))
    c = _client()
    ok = c.post("/api/analysis/image", files={"file": ("x.png", make_image(), "application/octet-stream")},
                data={"type": "xray", "language": "hi"})
    assert ok.status_code == 200 and ok.json()["status"] == "ok"   # wrong Content-Type is fine: bytes are sniffed

    pdf = c.post("/api/analysis/image", files={"file": ("r.pdf", b"%PDF-1.4 hi", "application/pdf")}, data={"type": "xray"})
    assert pdf.status_code == 422 and "Report Summarizer" in pdf.json()["detail"]

    bad_type = c.post("/api/analysis/image", files={"file": ("x.png", make_image(), "image/png")}, data={"type": "nope"})
    assert bad_type.status_code == 400

    use_transport(monkeypatch, lambda r: httpx.Response(401, json={"error": {"message": "bad"}}))
    down = c.post("/api/analysis/image", files={"file": ("x.png", make_image(), "image/png")}, data={"type": "xray"})
    assert down.status_code == 503 and isinstance(down.json()["detail"], str) and down.json()["attempts"]


def test_http_status_endpoint():
    body = _client().get("/api/analysis/status").json()
    assert body["vision_available"] is True and set(body["vision_providers"]) == {"anthropic", "openai", "groq"}


def test_groq_retired_model_falls_back_and_strips_thinking(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    seen = []
    def handler(request):
        model = json.loads(request.content)["model"]
        seen.append(model)
        if model == settings.GROQ_VISION_MODEL:
            return httpx.Response(404, json={"error": {"message": "model does not exist"}})
        txt = "<think>{not json} hmm</think>" + json.dumps(GOOD)
        return httpx.Response(200, json={"choices": [{"message": {"content": txt}}]})
    use_transport(monkeypatch, handler)
    result = run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert result["provider"] == "groq" and result["status"] == "ok"
    assert seen == [settings.GROQ_VISION_MODEL, settings.GROQ_VISION_FALLBACK_MODEL]


def test_no_credits_message(monkeypatch):
    use_transport(monkeypatch, lambda r: httpx.Response(400, json={"error": {"message": "Your credit balance is too low"}}))
    with pytest.raises(AnalysisError) as e:
        run(AnalysisService().analyze_bytes(make_image(), "xray"))
    assert "no credits left" in e.value.message
