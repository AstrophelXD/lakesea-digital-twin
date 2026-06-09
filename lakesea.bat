@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

if "%~1"=="" goto :menu
if /i "%~1"=="help" goto :help
if /i "%~1"=="setup" goto :setup
if /i "%~1"=="setup-dm8" goto :setup_dm8
if /i "%~1"=="run" goto :run
if /i "%~1"=="defense" goto :defense
if /i "%~1"=="defense-dm8" goto :defense_dm8
if /i "%~1"=="reset" goto :reset
if /i "%~1"=="test" goto :test
if /i "%~1"=="smoke" goto :smoke
echo [ERROR] Unknown command: %~1
goto :help

:banner
echo.
echo ========================================
echo   LakeSea Digital Twin - %~1
echo ========================================
echo.
exit /b 0

:require_venv
if exist "backend\.venv\Scripts\python.exe" exit /b 0
echo [ERROR] backend\.venv not found. Run: lakesea.bat setup
pause
exit /b 1

:ensure_frontend
if exist "frontend\node_modules\" exit /b 0
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
exit /b 0

:menu
call :banner "Command Menu"
echo   lakesea.bat setup         First setup (SQLite dev)
echo   lakesea.bat setup-dm8     First setup (DM8 defense)
echo   lakesea.bat run           Start backend + frontend
echo   lakesea.bat defense       Pre-defense: reset + start (SQLite)
echo   lakesea.bat defense-dm8   Pre-defense: reset + start (DM8)
echo   lakesea.bat reset         Reset demo DB only (--full)
echo   lakesea.bat test          Run pytest (16 cases, SQLite)
echo   lakesea.bat smoke         E2E smoke test (backend must run)
echo   lakesea.bat help          Show this help
echo.
echo   Tip: pass a command directly, e.g. lakesea.bat defense
echo.
pause
exit /b 0

:help
call :banner "Help"
echo Usage: lakesea.bat [command]
echo.
echo   setup         Create venv, install deps, seed SQLite, npm install
echo   setup-dm8     Venv + dmPython + copy .env.dm8.example, guide init_db.sql
echo   run           Start backend :8000 and frontend :5173, open browser
echo   defense       reset_demo_db --full + run (uses backend\.env)
echo   defense-dm8     Same as defense, expects DM8 DATABASE_URL in .env
echo   reset         python -m scripts.reset_demo_db --full only
echo   test          pytest in isolated test_lakesea.db (MOCK_AI=true)
echo   smoke         python -m scripts.smoke_test against running backend
echo.
echo Docs: docs\dm8-deployment.md  docs\demo-data.md  docs\demo-script.md
echo.
pause
exit /b 0

:setup
call :banner "First Setup (SQLite)"
set "PIP_PROXY=http://127.0.0.1:7897"
set "HTTP_PROXY=%PIP_PROXY%"
set "HTTPS_PROXY=%PIP_PROXY%"

echo [1/4] Create Python venv...
if not exist "backend\.venv\Scripts\python.exe" (
    pushd "backend"
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Install Python 3.11+
        popd
        pause
        exit /b 1
    )
    popd
) else (
    echo   backend\.venv already exists, skip
)

echo [2/4] Install backend packages...
pushd "backend"
call pip-install.bat --no-pause
if errorlevel 1 (
    popd
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
if not exist ".env" (
    echo [INFO] Copy .env.example to .env
    copy /y ".env.example" ".env" >nul
)
echo [3/4] Seed SQLite database...
python -m scripts.seed_db
if errorlevel 1 (
    echo [ERROR] seed_db failed
    popd
    pause
    exit /b 1
)
popd

echo [4/4] Install frontend packages...
call :ensure_frontend
if errorlevel 1 exit /b 1

echo.
echo Setup done. Next: lakesea.bat run
echo.
pause
exit /b 0

:setup_dm8
call :banner "First Setup (DM8)"
set "PIP_PROXY=http://127.0.0.1:7897"
set "HTTP_PROXY=%PIP_PROXY%"
set "HTTPS_PROXY=%PIP_PROXY%"

echo [1/5] Create Python venv...
if not exist "backend\.venv\Scripts\python.exe" (
    pushd "backend"
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Install Python 3.11+
        popd
        pause
        exit /b 1
    )
    popd
) else (
    echo   backend\.venv already exists, skip
)

echo [2/5] Install backend packages + dmPython...
pushd "backend"
call pip-install.bat --no-pause
if errorlevel 1 (
    popd
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
pip install dmPython
if errorlevel 1 (
    echo [WARN] pip install dmPython failed. Install from DM8 SDK if needed.
)

echo [3/5] Configure .env for DM8...
if not exist ".env" (
    copy /y ".env.dm8.example" ".env" >nul
    echo   Created backend\.env from .env.dm8.example
) else (
    echo   backend\.env already exists, not overwritten
    echo   Ensure DATABASE_URL uses dm+dmPython://...
)
echo.
echo [4/5] MANUAL: execute init_db.sql in DM8 Manager
echo   File: backend\scripts\init_db.sql
echo   Then edit backend\.env DATABASE_URL (user/password/schema)
echo.
set /p "DM8_READY=Have you run init_db.sql and set DATABASE_URL? (Y/N): "
if /i not "!DM8_READY!"=="Y" (
    echo.
    echo Stopped. After init_db.sql and .env, run:
    echo   lakesea.bat reset
    echo   lakesea.bat defense-dm8
    popd
    pause
    exit /b 0
)

echo [5/5] Seed / reset demo data on DM8...
python -m scripts.reset_demo_db --full
if errorlevel 1 (
    echo [ERROR] reset_demo_db failed. Check DM8 service and DATABASE_URL.
    popd
    pause
    exit /b 1
)
popd

call :ensure_frontend
if errorlevel 1 exit /b 1

echo.
echo DM8 setup done. Next: lakesea.bat defense-dm8
echo Full guide: docs\dm8-deployment.md
echo.
pause
exit /b 0

:run
call :banner "Start All"
call :require_venv
if errorlevel 1 exit /b 1

if not exist "backend\.env" (
    echo [INFO] Copying backend\.env.example to backend\.env
    copy /y "backend\.env.example" "backend\.env" >nul
)

call :ensure_frontend
if errorlevel 1 exit /b 1

echo [1/3] Starting backend http://127.0.0.1:8000
start "LakeSea-Backend" cmd /k "cd /d "%ROOT%backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [2/3] Waiting for backend...
timeout /t 4 /nobreak >nul

echo [3/3] Starting frontend http://localhost:5173
start "LakeSea-Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo Started. Login: admin / 123456
echo Health: http://127.0.0.1:8000/api/health/db
echo.
pause
exit /b 0

:defense
call :banner "Pre-Defense (SQLite)"
call :require_venv
if errorlevel 1 exit /b 1

if not exist "backend\.env" (
    copy /y "backend\.env.example" "backend\.env" >nul
)

call :ensure_frontend
if errorlevel 1 exit /b 1

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

goto :start_after_reset

:defense_dm8
call :banner "Pre-Defense (DM8)"
call :require_venv
if errorlevel 1 exit /b 1

if not exist "backend\.env" (
    echo [ERROR] backend\.env not found. Run: lakesea.bat setup-dm8
    pause
    exit /b 1
)

findstr /i /c:"dm+dmpython" "backend\.env" >nul
if errorlevel 1 (
    echo [WARN] backend\.env may not be DM8. Check DATABASE_URL.
)

call :ensure_frontend
if errorlevel 1 exit /b 1

echo [TIP] Ensure DmService is running before reset.
echo.
echo [1/4] Resetting DM8 demo data (--full)...
pushd "backend"
call .venv\Scripts\activate.bat
python -m scripts.reset_demo_db --full
if errorlevel 1 (
    echo [ERROR] reset_demo_db failed. Check DM8 connection.
    popd
    pause
    exit /b 1
)
popd

:start_after_reset
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
echo   Pre-defense ready.
echo ----------------------------------------
echo   Frontend  http://localhost:5173
echo   Backend   http://127.0.0.1:8000
echo   DB health http://127.0.0.1:8000/api/health/db
echo ----------------------------------------
echo   Accounts (password 123456):
echo     admin director01 teacher01 student01 maintainer01
echo ----------------------------------------
echo   Demo: 10 resources, 3 reservations, archived task + AI
echo   Guide: docs\demo-script.md
echo ========================================
echo.
pause
exit /b 0

:reset
call :banner "Reset Demo DB"
call :require_venv
if errorlevel 1 exit /b 1

echo [TIP] Close backend window if SQLite file is locked.
echo.
pushd "backend"
call .venv\Scripts\activate.bat
python -m scripts.reset_demo_db --full
if errorlevel 1 (
    echo [ERROR] reset failed
    popd
    pause
    exit /b 1
)
popd
echo.
echo Done. Run lakesea.bat run or lakesea.bat defense-dm8 to start services.
echo.
pause
exit /b 0

:test
call :banner "Pytest"
call :require_venv
if errorlevel 1 exit /b 1

pushd "backend"
call .venv\Scripts\activate.bat
python -m pytest tests/ -v --tb=short
set "TEST_EXIT=%ERRORLEVEL%"
popd
echo.
if "%TEST_EXIT%"=="0" (
    echo All tests passed.
) else (
    echo Some tests failed. Exit code: %TEST_EXIT%
)
pause
exit /b %TEST_EXIT%

:smoke
call :banner "Smoke Test"
call :require_venv
if errorlevel 1 exit /b 1

echo Requires backend at http://127.0.0.1:8000
echo.
pushd "backend"
call .venv\Scripts\activate.bat
python -m scripts.smoke_test
set "SMOKE_EXIT=%ERRORLEVEL%"
popd
pause
exit /b %SMOKE_EXIT%
