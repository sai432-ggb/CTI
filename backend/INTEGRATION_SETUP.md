# Frontend-Backend Integration Setup Guide

This guide explains how to connect the React/TanStack frontend to the FastAPI backend.

## Overview

Your project has two separate applications that need to communicate:
- **Frontend**: React app running on `localhost:3000` (TanStack Start)
- **Backend**: FastAPI app running on `localhost:8000` (Python)

## Setup Steps

### 1. Backend Setup

#### 1.1 Create Environment Variables

Copy the example file and add your API keys:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` and add your actual API keys:
```env
OPENAI_API_KEY="sk-your-real-key-here"
VIRUSTOTAL_API_KEY="your-real-key-here"
ABUSEIPDB_API_KEY="your-real-key-here"
```

#### 1.2 Install Dependencies

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### 1.3 Run the Backend

**Option A: Direct with Uvicorn**
```bash
uvicorn app.main:app --reload --port 8000
```

**Option B: With Docker**
```bash
docker-compose up --build
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

#### 2.1 Create Environment Variables

Copy the example file:

```bash
cd ..  # Go back to project root
cp .env.example .env
```

Edit `.env` and ensure the backend URL is correct:
```env
VITE_API_BASE_URL=http://localhost:8000
```

#### 2.2 Install Dependencies

```bash
npm install
# or
bun install
```

#### 2.3 Run the Frontend

```bash
npm run dev
# or
bun run dev
```

The frontend will be available at `http://localhost:3000`

## How They Connect

### Frontend API Calls

The frontend uses the `api.ts` client to make requests:

```typescript
// src/lib/api.ts uses VITE_API_BASE_URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Example usage:
import { api } from '@/lib/api';

const result = await api.analyzeUrl('https://example.com');
```

### Backend CORS Configuration

The backend allows requests from frontend URLs configured in `.env`:

```python
# backend/app/main.py reads FRONTEND_URLS from environment
FRONTEND_URLS="http://localhost:3000"  # comma-separated for multiple origins
```

In production, update this to:
```env
FRONTEND_URLS="https://your-app.pages.dev,https://your-domain.com"
```

## Testing the Connection

### 1. Verify Backend is Running

Open browser or terminal:
```bash
curl http://localhost:8000
# Should return: {"status": "CTI Backend is running natively."}
```

### 2. Check Frontend API Client

Open browser console and test:
```javascript
import { api } from '@/lib/api';

// Test connection
const health = await api.healthCheck();
console.log(health);  // Should show: {status: "CTI Backend is running natively."}

// Test URL analysis
const result = await api.analyzeUrl('https://example.com');
console.log(result);
```

## Troubleshooting

### CORS Error
**Error**: `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution**:
1. Verify backend is running on correct port
2. Check `FRONTEND_URLS` in `backend/.env` matches your frontend URL
3. Restart the backend after changing `.env`

### API Not Found
**Error**: `404 Not Found` when calling API endpoints

**Solution**:
1. Verify backend is running: `http://localhost:8000`
2. Check endpoint exists in `backend/app/routers/analysis.py`
3. Verify the endpoint path in `src/lib/api.ts` matches

### Database Locked
**Error**: `database is locked`

**Solution**:
1. Make sure only one backend instance is running
2. Delete `cti_dashboard.db` to reset: `rm cti_dashboard.db`
3. Restart backend

## Production Deployment

### Frontend (Cloudflare Pages)

1. Update `.env` for production:
```env
VITE_API_BASE_URL=https://your-backend-domain.com
```

2. Build and deploy:
```bash
npm run build
# Deploy dist folder to Cloudflare Pages
```

### Backend (Railway / AWS Lambda / Heroku)

1. Update `backend/.env` for production:
```env
DATABASE_URL="postgresql://..."  # Use PostgreSQL
FRONTEND_URLS="https://your-frontend.pages.dev"
SECRET_KEY="<generate-strong-key>"
```

2. Deploy with Docker:
```bash
docker build -t cti-backend .
docker push your-registry/cti-backend:latest
```

3. On your platform (Railway/AWS/Heroku):
   - Set environment variables from `.env`
   - Deploy the Docker image
   - Get the deployed URL (e.g., `https://cti-backend.railway.app`)

4. Update frontend `.env` with production backend URL

## Environment Variables Summary

### Frontend (.env)
| Variable | Value | Example |
|----------|-------|---------|
| VITE_API_BASE_URL | Backend URL | http://localhost:8000 |

### Backend (.env)
| Variable | Purpose | Example |
|----------|---------|---------|
| OPENAI_API_KEY | GPT-4 access for NLP | sk-... |
| VIRUSTOTAL_API_KEY | Threat intel API | ... |
| ABUSEIPDB_API_KEY | IP reputation API | ... |
| DATABASE_URL | Database connection | sqlite:///./cti_dashboard.db |
| FRONTEND_URLS | Allowed origins | http://localhost:3000 |
| SECRET_KEY | JWT signing key | random-string |

## Next Steps

1. ✅ Set up `.env` files with API keys
2. ✅ Run backend: `uvicorn app.main:app --reload`
3. ✅ Run frontend: `npm run dev`
4. ✅ Test API calls from browser console
5. Build real backend endpoints in `backend/app/routers/`
6. Replace client-side analyzers with backend API calls
7. Deploy to production
