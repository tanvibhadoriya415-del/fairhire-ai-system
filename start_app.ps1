# FairHire AI - PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting FairHire AI (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$projectRoot = "C:\Users\91930\Desktop\Cornerstone_project"
Set-Location $projectRoot

# 1. Start Backend in separate window
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projectRoot'; .\.venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 2

# 2. Start Frontend in separate window
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projectRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

# 3. Automatically open in browser
Start-Process "http://localhost:5173"

Write-Host "`nProject launched! The web page has opened in your browser." -ForegroundColor Yellow
Write-Host "  -> Web App:      http://localhost:5173" -ForegroundColor White
Write-Host "  -> Backend API:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  -> Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
