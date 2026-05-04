@echo off
chcp 65001 >nul
echo ======================================
echo   AI Novelist
echo ======================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Check port conflicts
echo [0/3] Checking ports...
netstat -ano 2>nul | findstr ":8000 " >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 8000 is already in use. Backend may fail to start.
)
netstat -ano 2>nul | findstr ":3000 " >nul
if %errorlevel% equ 0 (
    echo [WARN] Port 3000 is already in use. Frontend may fail to start.
)

:: Check .env
if not exist .env (
    echo [INFO] .env not found, copying from .env.example...
    copy .env.example .env
    echo Please edit .env and fill in your API Key before starting.
    echo.
    notepad .env
    echo Press any key after saving .env...
    pause >nul
)

:: Install backend deps
echo [1/3] Installing backend dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo Backend dependency install failed
    pause
    exit /b 1
)

:: Install frontend deps
echo [2/3] Installing frontend dependencies...
cd frontend
call npm install --silent
if %errorlevel% neq 0 (
    cd ..
    echo Frontend dependency install failed
    pause
    exit /b 1
)
cd ..

:: Create data dir
if not exist data mkdir data

echo.
echo [3/3] Starting services...
echo   Backend API: http://localhost:8000
echo   Frontend UI: http://localhost:3000
echo.
echo Open browser: http://localhost:3000
echo.

:: Start backend (background)
start "AI Novelist Backend" cmd /c "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start frontend
cd frontend
npx vite --host --port 3000
