@echo off
REM ============================================================================
REM  MixMind DJ — one-click launcher for Windows
REM  Sets up venv, installs deps, seeds demo, starts API + frontend.
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo  =====================================================
echo   MixMind DJ — Starting
echo  =====================================================
echo.

cd /d "%~dp0"

REM --- 1. Backend venv ---
if not exist backend\venv (
    echo [1/5] Creating Python virtual environment...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo  ERROR: failed to create venv. Is Python 3.11+ installed?
        echo  Download: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    cd ..
) else (
    echo [1/5] Backend venv already exists
)

REM --- 2. Install backend deps if missing ---
echo [2/5] Installing Python dependencies...
call backend\venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r backend\requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo  ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

REM --- 3. Health check ---
echo [3/5] Running health check...
cd backend
python -m mixmind health
if errorlevel 1 (
    echo.
    echo  ERROR: health check failed.
    pause
    exit /b 1
)
cd ..

REM --- 4. Frontend deps ---
echo [4/5] Installing frontend dependencies...
cd frontend
if not exist node_modules (
    call npm install
    if errorlevel 1 (
        echo.
        echo  ERROR: npm install failed. Is Node.js 20+ installed?
        echo  Download: https://nodejs.org/
        pause
        exit /b 1
    )
) else (
    echo Frontend node_modules already present
)
cd ..

REM --- 5. Seed demo data if library is empty ---
cd backend
for /f "tokens=*" %%a in ('python -m mixmind stats ^| findstr /C:"Total tracks:"') do set TRACKS=%%a
echo %TRACKS% | findstr /C:"Total tracks: 0" >nul
if not errorlevel 1 (
    echo [5/5] Library is empty — seeding 60 demo tracks...
    python -m mixmind demo
) else (
    echo [5/5] Library already has data
)
cd ..

echo.
echo  =====================================================
echo   Launching MixMind DJ
echo   Backend: http://127.0.0.1:8000
echo   Web UI:  http://localhost:5173
echo  =====================================================
echo.

REM Start backend in a new window
start "MixMind Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn mixmind.api:app --reload"

REM Wait a moment for backend to come up
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "MixMind Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Open the browser
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo Both servers started in separate windows.
echo Close those windows to stop the servers.
echo.
pause
