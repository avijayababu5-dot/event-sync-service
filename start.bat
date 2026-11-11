@echo off
start "Event Sync API" cmd /k "cd backend && if not exist .venv python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --reload"
start "Event Sync UI" cmd /k "cd frontend && npm install && npm run dev"
