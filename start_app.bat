@echo off
echo ===================================================
echo Starting FairHire AI (Backend + Frontend)
echo ===================================================

cd /d "C:\Users\91930\Desktop\Cornerstone_project"

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "FairHire AI - Backend API" cmd /k ".\.venv\Scripts\activate.bat && python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
start "FairHire AI - Frontend Web App" cmd /k "cd frontend && npm run dev"

timeout /t 2 /nobreak >nul

start http://localhost:5173

echo.
echo Both servers have been launched and opened in your browser!
echo - Frontend: http://localhost:5173
echo - Backend API: http://127.0.0.1:8000
echo - Swagger Docs: http://127.0.0.1:8000/docs
echo ===================================================
