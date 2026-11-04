# Image & Report Analysis — how it works

**Pipeline:** upload → `image_utils.prepare_image` (detect real format, fix rotation, 16-bit/BMP/RGBA → 8-bit JPEG,
resize ≤1568px, <4 MB, strip metadata, quality checks) → `vision_providers.run_chain`
(Anthropic → OpenAI → Groq, async, retry + model fallback) → `analysis_service` (structured JSON, validation,
confidence capped by image quality) → UI.

**No fake results.** If every provider fails the API returns HTTP 503 with the reason per provider
(`{"detail": "...", "attempts": [{"provider": "openai", "reason": "API key was rejected ..."}]}`),
and the page offers a **Test AI connection** button (`GET /api/analysis/diagnose`).

**Setup:** put at least one of `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` in `backend/.env`, restart the backend.
Then `pip install -r requirements.txt` (adds `pypdf`) and run `pytest tests/test_image_analysis.py` (no DB / no API calls needed).

**Endpoints**
- `GET  /api/analysis/status`   — configured providers (no API calls)
- `GET  /api/analysis/diagnose` — live test of each provider (login required)
- `POST /api/analysis/image`    — form: `file`, `type` (xray|scan|skin|report), `language`
- `POST /api/analysis/report`   — form: `file` (PDF / image / txt), `language`

Not a medical device. Output is informational and always carries a disclaimer.
