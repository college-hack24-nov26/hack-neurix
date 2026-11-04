> **Legacy document.** This guide describes the previous MongoDB version of HomeCare+.
> For the current PostgreSQL setup see the top-level `README.md` and `POSTGRES_MIGRATION.md`.

# HomeCare+ Healthcare AI Platform - Complete Setup Guide

## 🎯 What's New (IMPROVED Version)

✅ **Real AI Integration**
- OpenAI GPT-4 (best quality)
- Anthropic Claude (high quality fallback)
- Groq API (fast alternative)
- Automatic fallback system

✅ **Multi-Language Support (11 Languages)**
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Kannada (kn)
- Malayalam (ml)
- Marathi (mr)
- Gujarati (gu)
- Urdu (ur)
- Bengali (bn)
- Punjabi (pa)

✅ **Enhanced Features**
- Real medical AI responses (not rule-based)
- Language-aware system prompts
- Better error handling & logging
- Streaming response support
- Multi-model fallback chain
- Medical context-aware responses

---

## 🔧 Prerequisites

### System Requirements
- **OS:** Windows/Mac/Linux
- **Node.js:** v16+ (for frontend)
- **Python:** 3.9+ (for backend)
- **MongoDB:** Local or cloud (Atlas)
- **RAM:** 4GB minimum
- **Internet:** Required for AI API calls

### Required Accounts (Choose at least one)
1. **OpenAI** - https://platform.openai.com (RECOMMENDED)
   - Best quality responses
   - $0.001-0.003 per request (very cheap)
   
2. **Anthropic** - https://console.anthropic.com
   - High quality alternative
   - Good for image analysis
   
3. **Groq** - https://console.groq.com
   - Free tier available
   - Fast responses
   - Good for testing

4. **MongoDB Atlas** - https://www.mongodb.com/cloud/atlas
   - Free tier: 512MB storage
   - Cloud database (recommended)

---

## 📦 Installation Steps

### Step 1: Clone/Extract Project
```bash
# If you have the zip file
unzip homecare-plus-improved.zip
cd homecare-plus-improved
```

### Step 2: Backend Setup

#### 2.1 Install Python Dependencies
```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2.2 Create `.env` File
Create `backend/.env` with your API keys:

```env
# ─── MongoDB Configuration ───────────────────────
MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/homecare?retryWrites=true&w=majority
MONGO_DB_NAME=homecare
MONGO_TIMEOUT=10000

# ─── AI API Keys (Choose at least ONE) ────────────

# OpenAI (RECOMMENDED - Best Quality)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_VISION_MODEL=claude-3-5-sonnet-20241022

# Groq (Free Alternative)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxx
GROQ_MODEL=mixtral-8x7b-32768

# ─── Server Configuration ──────────────────────
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
AI_REQUEST_TIMEOUT=30
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50
```

**How to Get API Keys:**

**OpenAI:**
1. Go to https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-`)
4. Paste in `.env`

**Anthropic:**
1. Go to https://console.anthropic.com/account/keys
2. Create new API key
3. Copy and paste in `.env`

**Groq:**
1. Go to https://console.groq.com/keys
2. Create API key
3. Copy and paste in `.env`

**MongoDB:**
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string: `mongodb+srv://user:pass@...`
4. Replace `username:password` with your credentials

#### 2.3 Run Backend
```bash
python main.py

# You should see:
# ✓ Connected to MongoDB...
# ✓ HomeCare+ backend started successfully
# ✓ Uvicorn running on http://0.0.0.0:8000
```

Backend will run on: **http://localhost:8000**
API Docs: **http://localhost:8000/api/docs**

---

### Step 3: Frontend Setup

#### 3.1 Install Dependencies
```bash
cd ../frontend
npm install
```

#### 3.2 Create `.env` File
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=HomeCare+
VITE_DEFAULT_LANGUAGE=en
```

#### 3.3 Run Frontend Development Server
```bash
npm run dev

# You should see:
# ✓ VITE ...
# ✓ Local: http://localhost:5173
```

Frontend will run on: **http://localhost:5173**

---

## 🚀 First Time Usage

### 1. Open Browser
```
http://localhost:5173
```

### 2. Create Account
- Email: `test@example.com`
- Password: Any password

### 3. Test AI Chat
1. Go to "AI Assistant"
2. Select Language (Hindi, English, etc.)
3. Ask: "मुझे सिरदर्द है" or "I have a headache"
4. Should get REAL AI response in selected language ✅

### 4. Test Multiple Languages
Switch language in settings → see responses in Hindi, Tamil, Telugu, etc.

---

## 🔍 Troubleshooting

### "Connection refused" - Backend not running
```bash
# Make sure you're in backend directory
cd backend
python main.py
```

### "MONGO_URI not found" - Missing .env file
```bash
# Create backend/.env with your MongoDB connection string
echo "MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/homecare" > .env
```

### "API key invalid" - Wrong OpenAI key
```bash
# Verify key format: should start with "sk-"
# Get new key from https://platform.openai.com/account/api-keys
```

### "Port 8000 already in use"
```bash
# Use different port
python main.py --port 8001
```

### "Module not found: anthropic"
```bash
pip install -r requirements.txt
pip install anthropic openai groq
```

### Chat responds in English but selected Hindi
- Backend is missing ANTHROPIC_API_KEY or OPENAI_API_KEY
- Add API key to `.env` and restart backend
- Check logs: `ai_powered: false` means using fallback

---

## 📊 Testing Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can create account and login
- [ ] Can send message in English → gets real AI response
- [ ] Can send message in Hindi → gets Hindi response
- [ ] Response starts with actual AI answer (not "Thank you for question")
- [ ] API logs show "✓ AI chat served by OpenAI" (not fallback)
- [ ] Can upload health records
- [ ] Can view symptom checker
- [ ] No console errors

---

## 💡 Pro Tips

### For Best Performance
```
1. Use OpenAI API (best quality)
2. Set OPENAI_MODEL=gpt-4o-mini (fast & cheap)
3. Keep TEMPERATURE=0.4 (medical accuracy)
4. Use MongoDB Atlas (reliable)
```

### Cost Optimization
```
OpenAI: $0.10 per 1M input tokens, $0.30 per 1M output tokens
- Average medical query: ~50 tokens input, ~200 tokens output
- Cost per response: ~$0.0002 (0.02 cents!)
- 1000 responses: ~$0.20
```

### Monitoring AI Calls
Check `backend/main.py` logs:
```
✓ AI chat served by OpenAI (gpt-4o-mini)      ← Real AI
✓ AI chat served by Anthropic (claude...)      ← Fallback
✓ AI chat served by Groq (mixtral...)          ← Last resort
⚠ No AI provider configured                    ← Using rule-based
```

---

## 📁 Project Structure

```
homecare-plus-improved/
├── backend/
│   ├── main.py                 ← Start here
│   ├── requirements.txt         ← Python packages
│   ├── .env                     ← API keys (YOU CREATE)
│   ├── app/
│   │   ├── routes/
│   │   │   └── chat.py         ← AI chat endpoint
│   │   └── services/
│   │       └── ai_service.py   ← AI logic (IMPROVED)
│   └── seed_diseases.py         ← Database seeder
│
├── frontend/
│   ├── src/
│   │   ├── i18n_enhanced.js    ← 11 languages (NEW)
│   │   ├── pages/
│   │   │   └── Chat.jsx        ← Chat UI
│   │   └── App.jsx
│   ├── package.json
│   ├── .env                     ← Frontend config (YOU CREATE)
│   └── vite.config.js
│
└── SETUP_GUIDE.md              ← This file
```

---

## 🎓 Understanding the AI Flow

```
User asks in Hindi → Frontend sends to backend
                ↓
Backend receives: { language: "hi", message: "सिरदर्द है" }
                ↓
AIService checks API keys in order:
  1. OpenAI configured? → Call with Hindi system prompt ✓
  2. No OpenAI → Try Anthropic
  3. No Anthropic → Try Groq
  4. All failed → Use rule-based response
                ↓
AI responds in Hindi with medical information
                ↓
Response saved to MongoDB
                ↓
Frontend displays response ✓
```

---

## 🔐 Security Notes

⚠️ **Production Deployment:**
1. Never commit `.env` to git
2. Use environment variables in production
3. Set `DEBUG=false`
4. Use `ALLOWED_ORIGINS` correctly
5. Enable HTTPS
6. Rotate JWT_SECRET_KEY
7. Use environment-specific API keys

---

## 📞 Support

- **API Docs:** http://localhost:8000/api/docs (Swagger UI)
- **Health Check:** http://localhost:8000/api/health-check
- **OpenAI Help:** https://platform.openai.com/docs
- **MongoDB Help:** https://docs.mongodb.com

---

## ✨ What Makes This Version "Real AI"

| Feature | Before | After |
|---------|--------|-------|
| AI Response | Rule-based (fake) | Real GPT-4/Claude |
| Languages | English only | 11 languages |
| Medical Info | Hardcoded | AI-generated |
| Updates | Manual | Real-time |
| Quality | Limited | Professional |
| Cost | Free | $0.0002 per response |

---

**Last Updated:** June 2026
**Status:** ✅ Production Ready
**Version:** 2.0 (IMPROVED)
