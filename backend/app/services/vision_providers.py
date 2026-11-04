"""
HomeCare+ — LLM / vision provider chain (async, SDK-free).

Talks to Anthropic, OpenAI and Groq over plain HTTPS with httpx so that:
  * calls never block the FastAPI event loop (the old code used sync SDKs
    inside `async def` routes, freezing the whole server during analysis)
  * behaviour does not depend on pinned SDK versions
  * every failure is captured as a short, key-free reason that can be shown
    to the user ("OpenAI: quota exceeded") instead of silently returning a
    fake result.

Vision order is configurable (VISION_PROVIDER_ORDER, default
anthropic,openai,groq); text order is TEXT_PROVIDER_ORDER.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import httpx

from app.config.settings import settings, is_real_key

logger = logging.getLogger(__name__)

# Tests inject an httpx.MockTransport here; production leaves it as None.
_transport: Optional[httpx.AsyncBaseTransport] = None

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class LLMRequest:
    system: str
    prompt: str
    image_b64: Optional[str] = None
    image_media_type: str = "image/jpeg"
    pdf_b64: Optional[str] = None
    max_tokens: int = 2500
    expect_json: bool = True

    @property
    def is_vision(self) -> bool:
        return bool(self.image_b64 or self.pdf_b64)


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    elapsed_ms: int


class ProviderError(Exception):
    def __init__(self, provider: str, reason: str, *, retryable: bool = False,
                 model_missing: bool = False, status: Optional[int] = None):
        super().__init__(reason)
        self.provider = provider
        self.reason = reason
        self.retryable = retryable
        self.model_missing = model_missing
        self.status = status


class AllProvidersFailed(Exception):
    def __init__(self, attempts: List[dict], *, none_configured: bool = False):
        super().__init__("all providers failed")
        self.attempts = attempts
        self.none_configured = none_configured


# ── Provider registry ─────────────────────────────────────────────────────────

def _dedupe(models: List[str]) -> List[str]:
    out: List[str] = []
    for m in models:
        if m and m not in out:
            out.append(m)
    return out


def _key(provider: str) -> str:
    return {
        "anthropic": settings.ANTHROPIC_API_KEY,
        "openai": settings.OPENAI_API_KEY,
        "groq": settings.GROQ_API_KEY,
    }[provider]


def _models(provider: str, vision: bool) -> List[str]:
    if provider == "anthropic":
        primary = settings.ANTHROPIC_VISION_MODEL if vision else settings.ANTHROPIC_MODEL
        return _dedupe([primary, settings.ANTHROPIC_FALLBACK_MODEL])
    if provider == "openai":
        return [settings.OPENAI_VISION_MODEL if vision else settings.OPENAI_MODEL]
    if vision:
        return _dedupe([settings.GROQ_VISION_MODEL, settings.GROQ_VISION_FALLBACK_MODEL])
    return [settings.GROQ_MODEL]


def configured_providers(vision: bool, *, needs_pdf: bool = False) -> List[str]:
    raw = settings.VISION_PROVIDER_ORDER if vision else settings.TEXT_PROVIDER_ORDER
    order = [p.strip().lower() for p in raw.split(",") if p.strip()]
    result = []
    for p in order:
        if p not in ("anthropic", "openai", "groq"):
            continue
        if not is_real_key(_key(p)):
            continue
        if needs_pdf and p != "anthropic":      # only Anthropic reads PDFs natively
            continue
        result.append(p)
    return result


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(settings.AI_VISION_TIMEOUT, connect=10.0)
    return httpx.AsyncClient(timeout=timeout, transport=_transport)


def _error_message(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        err = body.get("error", body)
        if isinstance(err, dict):
            msg = err.get("message") or err.get("type") or str(err)
        else:
            msg = str(err)
    except Exception:
        msg = resp.text or ""
    msg = " ".join(str(msg).split())[:220]
    for k in (settings.ANTHROPIC_API_KEY, settings.OPENAI_API_KEY, settings.GROQ_API_KEY):
        if k and k in msg:
            msg = msg.replace(k, "***")
    return msg


def _raise_for_status(provider: str, model: str, resp: httpx.Response) -> None:
    if resp.status_code < 400:
        return
    st = resp.status_code
    msg = _error_message(resp)
    low = msg.lower()
    if st != 401 and ("credit balance" in low or "billing" in low or "insufficient_quota" in low or "no credits" in low):
        raise ProviderError(provider, "no credits left on this account — add credits in the provider's billing page", status=st)
    if st in (401, 403):
        raise ProviderError(provider, "API key was rejected — check the key in backend/.env", status=st)
    if st == 402:
        raise ProviderError(provider, "billing/credits problem on this account", status=st)
    if st == 404:
        raise ProviderError(provider, f"model '{model}' is not available for this key", model_missing=True, status=st)
    if st == 413:
        raise ProviderError(provider, "image is too large for this provider", status=st)
    if st == 429:
        raise ProviderError(provider, f"rate limit or quota exceeded ({msg})", retryable=True, status=st)
    if st in (408, 409, 500, 502, 503, 504, 529):
        raise ProviderError(provider, f"provider temporarily unavailable (HTTP {st})", retryable=True, status=st)
    raise ProviderError(provider, f"request rejected (HTTP {st}): {msg}", status=st)


# ── Provider calls ────────────────────────────────────────────────────────────

async def _call_anthropic(client: httpx.AsyncClient, req: LLMRequest, model: str) -> str:
    content: List[dict] = []
    if req.image_b64:
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": req.image_media_type, "data": req.image_b64}})
    if req.pdf_b64:
        content.append({"type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": req.pdf_b64}})
    content.append({"type": "text", "text": req.prompt})

    body = {
        "model": model,
        "max_tokens": req.max_tokens,
        "system": req.system,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY.strip(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = await client.post(ANTHROPIC_URL, headers=headers, json=body)
    _raise_for_status("anthropic", model, resp)
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


async def _call_openai_compatible(
    client: httpx.AsyncClient, provider: str, req: LLMRequest, model: str
) -> str:
    if provider == "openai":
        url, key, token_param = OPENAI_URL, settings.OPENAI_API_KEY, "max_completion_tokens"
    else:
        url, key, token_param = GROQ_URL, settings.GROQ_API_KEY, "max_tokens"

    if req.image_b64:
        data_url = f"data:{req.image_media_type};base64,{req.image_b64}"
        if provider == "groq":
            # Groq's vision models are most reliable with everything in one user turn.
            messages = [{"role": "user", "content": [
                {"type": "text", "text": f"{req.system}\n\n{req.prompt}"},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]}]
        else:
            messages = [
                {"role": "system", "content": req.system},
                {"role": "user", "content": [
                    {"type": "text", "text": req.prompt},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                ]},
            ]
    else:
        messages = [{"role": "system", "content": req.system}, {"role": "user", "content": req.prompt}]

    max_tokens = max(req.max_tokens, 4000) if provider == "groq" else req.max_tokens   # room for "thinking"
    body: Dict = {"model": model, "messages": messages, token_param: max_tokens}
    if req.expect_json:
        body["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {key.strip()}", "Content-Type": "application/json"}
    resp = await client.post(url, headers=headers, json=body)

    # Some models reject JSON mode; retry once without it (we parse JSON ourselves anyway).
    if resp.status_code == 400 and req.expect_json:
        low = resp.text.lower()
        if "response_format" in low or "json" in low:
            body.pop("response_format", None)
            resp = await client.post(url, headers=headers, json=body)

    _raise_for_status(provider, model, resp)
    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"] or ""
        # Reasoning models may inline their chain of thought; it is not part of the answer.
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return content
    except (KeyError, IndexError, TypeError):
        raise ProviderError(provider, "unexpected response format from provider")


async def _call(client: httpx.AsyncClient, provider: str, req: LLMRequest, model: str) -> str:
    if provider == "anthropic":
        return await _call_anthropic(client, req, model)
    return await _call_openai_compatible(client, provider, req, model)


async def run_single(provider: str, req: LLMRequest) -> LLMResult:
    """Run one provider (trying its fallback model names and one retry on transient errors)."""
    last: Optional[ProviderError] = None
    async with _client() as client:
        for model in _models(provider, req.is_vision):
            for attempt in (1, 2):
                started = time.monotonic()
                try:
                    text = await _call(client, provider, req, model)
                    if not text.strip():
                        raise ProviderError(provider, "provider returned an empty response", retryable=True)
                    return LLMResult(text=text, provider=provider, model=model,
                                     elapsed_ms=int((time.monotonic() - started) * 1000))
                except ProviderError as e:
                    last = e
                    if e.model_missing:
                        break                       # try the next model name
                    if e.retryable and attempt == 1:
                        await asyncio.sleep(1.5)
                        continue
                    raise
                except httpx.TimeoutException:
                    last = ProviderError(provider, f"timed out after {settings.AI_VISION_TIMEOUT}s", retryable=True)
                    if attempt == 1:
                        continue
                    raise last
                except httpx.HTTPError as e:
                    last = ProviderError(provider, f"network error ({type(e).__name__})", retryable=True)
                    if attempt == 1:
                        await asyncio.sleep(1.0)
                        continue
                    raise last
    raise last or ProviderError(provider, "no model available")


async def run_chain(req: LLMRequest) -> LLMResult:
    """Try each configured provider in order. Raises AllProvidersFailed with per-provider reasons."""
    providers = configured_providers(req.is_vision, needs_pdf=bool(req.pdf_b64))
    if not providers:
        raise AllProvidersFailed([], none_configured=True)

    attempts: List[dict] = []
    for p in providers:
        try:
            result = await run_single(p, req)
            logger.info("AI call served by %s (%s) in %d ms", result.provider, result.model, result.elapsed_ms)
            return result
        except ProviderError as e:
            logger.warning("Provider %s failed: %s", p, e.reason)
            attempts.append({"provider": p, "reason": e.reason})
        except Exception as e:                       # never let one provider crash the chain
            logger.exception("Provider %s crashed", p)
            attempts.append({"provider": p, "reason": f"unexpected error ({type(e).__name__})"})
    raise AllProvidersFailed(attempts)


# ── Diagnostics ───────────────────────────────────────────────────────────────

def _probe_image_b64() -> str:
    import io
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (160, 160), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.ellipse((40, 40, 120, 120), fill=(220, 220, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.standard_b64encode(buf.getvalue()).decode("ascii")


async def diagnose() -> List[dict]:
    """Send a tiny test image to every configured vision provider and report the outcome."""
    req = LLMRequest(
        system="You are a connectivity test.",
        prompt="Reply with the single word OK.",
        image_b64=_probe_image_b64(),
        max_tokens=16,
        expect_json=False,
    )
    report: List[dict] = []
    for p in configured_providers(vision=True):
        try:
            r = await run_single(p, req)
            report.append({"provider": p, "ok": True, "model": r.model, "latency_ms": r.elapsed_ms})
        except ProviderError as e:
            report.append({"provider": p, "ok": False, "reason": e.reason})
        except Exception as e:
            report.append({"provider": p, "ok": False, "reason": f"unexpected error ({type(e).__name__})"})
    return report
