@echo off
echo ================================================================
echo Starting Cost-Aware Multi-Tier Cascading Router System
echo ================================================================

echo 1. Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Backend Server" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo 2. Starting Next.js SaaS Frontend on http://localhost:3000 ...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo Both services started! Open http://localhost:3000 in your browser.
