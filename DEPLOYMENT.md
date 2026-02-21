# Realtor AI MVP — Deployment Guide

## Option 1: Railway (Recommended - Easiest)

1. Push code to GitHub:
```bash
cd /Users/codyshort/ClawWork
git init
git add realtor_mvp.py cli_wrapper_proxy.py requirements.txt
git commit -m "Realtor AI MVP - Initial deployment"
git remote add origin https://github.com/YOUR-USERNAME/realtor-mvp.git
git push -u origin main
```

2. Deploy to Railway:
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Select your repo
   - Railway auto-detects Python
   - Add environment variables in Railway dashboard:
     - `OPENAI_API_BASE=http://localhost:8001/v1` (for local testing)
     - Or use production proxy URL
   - Click Deploy

3. Railway provides a free tier (~$5/month for production)

## Option 2: Render

1. Same GitHub setup as above
2. Go to https://render.com
3. "New+" → "Web Service" → "Deploy from GitHub repo"
4. Name: `realtor-mvp`
5. Runtime: `Python 3.11`
6. Build: `pip install -r requirements.txt`
7. Start: `uvicorn realtor_mvp:app --host 0.0.0.0 --port $PORT`
8. Free tier available (~$7/month for uptime)

## Option 3: Docker + Any Cloud

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY realtor_mvp.py cli_wrapper_proxy.py .
CMD ["uvicorn", "realtor_mvp:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy to: AWS ECS, Google Cloud Run, Azure Container Instances (~$10-15/month)

## Production Architecture

```
┌─────────────────────────────────────────┐
│ Real Estate Agents (web or API)         │
└─────────────────────┬───────────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │  Realtor MVP (Railway)  │
         │  :8000/api/generate-*   │
         └────────────┬────────────┘
                      │
                      ▼
    ┌──────────────────────────────────┐
    │ CLI Wrapper Proxy (Local or Cloud)│
    │ :8001/v1/chat/completions       │
    └────────────┬─────────────────────┘
                 │
    ┌────┬───────┴────────┬───────┐
    ▼    ▼                ▼       ▼
  Claude Gemini Kimi    Codex
  (subscription CLIs - ZERO API COST)
```

## Testing Before Deployment

```bash
# Test locally
curl -X POST http://localhost:8080/api/generate-description \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Main St",
    "bedrooms": 3,
    "bathrooms": 2,
    "sqft": 2400,
    "price": 500000,
    "year_built": 2010,
    "features": ["Updated kitchen"],
    "neighborhood": "Downtown"
  }'

# Test production
curl -X POST https://your-app.railway.app/api/generate-description \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Environment Variables Needed

```
# Production environment
OPENAI_API_BASE=https://your-cli-wrapper-proxy.app/v1
OPENAI_API_KEY=sk-clawwork-proxy
CLI_WRAPPER_TIMEOUT=60
```

## Cost Breakdown

- **Railway/Render**: $5-7/month
- **CLI Wrapper Proxy**: $0 (uses your subscriptions)
- **Custom Domain**: $12/year (optional)
- **Total First Year**: ~$75 + domain (~$87 total)

## Next Steps

1. Deploy to Railway (takes 5 minutes)
2. Get custom domain (realtorai.app or similar)
3. Create landing page
4. Start outreach to real estate agents
5. First customer in 7 days → $500-1000/month
