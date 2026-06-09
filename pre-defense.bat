@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ========================================
echo   LakeSea - Pre-Defense Setup
echo   Reset demo data + Start services
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

echo [TIP] Close LakeSea-Backend window if open, for cleanest DB reset.
echo.
echo [1/4] Resetting demo database (--full)...
pushd "backend"
call .venv\Scripts\activate.bat
python -m scripts.reset_demo_db --full
if errorlevel 1 (
    echo [ERROR] reset_demo_db failed
    popd
    pause
    exit /b 1
)
popd
echo.

echo [2/4] Starting backend http://127.0.0.1:8000
start "LakeSea-Backend" cmd /k "cd /d "%ROOT%backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [3/4] Waiting for backend...
timeout /t 4 /nobreak >nul

echo [4/4] Starting frontend http://localhost:5173
start "LakeSea-Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo ========================================
echo   Pre-defense setup complete.
echo ----------------------------------------
echo   Frontend  http://localhost:5173
echo   Backend   http://127.0.0.1:8000
echo   API docs  http://127.0.0.1:8000/docs
echo ----------------------------------------
echo   Accounts (password 123456 for all):
echo     admin        - Administrator
echo     director01   - Director
echo     teacher01    - Teacher
echo     student01    - Student
echo     maintainer01 - Maintainer
echo ----------------------------------------
echo   Demo data loaded:
echo     10 resources, 3 reservations
echo     TASK-DEMO-ARCHIVED (archive + AI)
echo     RSV-DEMO-PENDING (director approval)
echo     RSV-DEMO-DRAFT   (student submit)
echo ----------------------------------------
echo   Demo guide: docs\demo-script.md
echo ========================================
echo.
pause
