@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ========================================
echo   LakeSea Digital Twin - Start All
echo ========================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] backend\.venv not found.
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "backend\.env" (
    echo [INFO] Copying backend\.env.example to backend\.env
    copy /y "backend\.env.example" "backend\.env" >nul
)

if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    pushd "frontend"
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed
        popd
        pause
        exit /b 1
    )
    popd
    echo.
)

echo [1/3] Starting backend http://127.0.0.1:8000
start "LakeSea-Backend" cmd /k "cd /d "%ROOT%backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [2/3] Waiting for backend...
timeout /t 4 /nobreak >nul

echo [3/3] Starting frontend http://localhost:5173
start "LakeSea-Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo ========================================
echo   Started. Keep both windows open.
echo ----------------------------------------
echo   Frontend  http://localhost:5173
echo   Backend   http://127.0.0.1:8000
echo   API docs  http://127.0.0.1:8000/docs
echo   Health    http://127.0.0.1:8000/api/health/db
echo ----------------------------------------
echo   Login     admin / 123456
echo ========================================
echo.
pause
