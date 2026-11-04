# 🚀 HomeCare+ — Quick Start (3 Steps)

## Step 1 — Add your API key (30 seconds)

Open **`backend/.env`** and paste your key:

```env
# Get free key from: https://console.groq.com/keys  (FREE)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# OR from: https://platform.openai.com/account/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
```

> Database: the default `DATABASE_URL=postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_plus` works with
> `docker compose up -d postgres` (then use port `5433` in the URL), or point it at any PostgreSQL 13+ / Neon / Supabase.
> After setting it, run `alembic upgrade head` once in `backend/` — the disease library loads automatically on first start.

---

## Step 2 — Start Backend

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac / Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

✅ You should see: `Uvicorn running on http://0.0.0.0:8000`

---

## Step 3 — Start Frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

✅ You should see: `Local: http://localhost:5173`

---

## 🎉 Open the app

→ **http://localhost:5173**

- Create an account → Login
- Go to **AI Assistant**
- Select **Hindi** from Settings → Language
- Ask: `मुझे सिरदर्द है` → Real AI response in Hindi ✅

---

## 🌍 Supported AI Response Languages (12)

Choose a response language in **Settings → Language**. Select **Hinglish** for Hindi written in Latin/English letters.

| Code | Language |
|------|----------|
| en | English |
| hi | हिंदी (Hindi) |
| hi-latn | Hinglish (Hindi in Latin/Roman script) |
| mr | मराठी (Marathi) |
| ta | தமிழ் (Tamil) |
| te | తెలుగు (Telugu) |
| kn | ಕನ್ನಡ (Kannada) |
| ml | മലയാളം (Malayalam) |
| gu | ગુજરાતી (Gujarati) |
| bn | বাংলা (Bengali) |
| pa | ਪੰਜਾਬੀ (Punjabi) |
| ur | اردو (Urdu) |

---

## 🆘 Quick Fixes

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Connection refused` | Backend not running — run `python main.py` |
| AI gives generic reply | Add API key to `backend/.env` |
| Database connection error | Check `DATABASE_URL`; run `alembic upgrade head` |
| Port 8000 busy | `lsof -i :8000` then kill the process |
| npm errors | Delete `node_modules/` then `npm install` |

---

API Docs (Swagger): **http://localhost:8000/api/docs**
