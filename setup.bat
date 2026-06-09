@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "PIP_PROXY=http://127.0.0.1:7897"
set "HTTP_PROXY=%PIP_PROXY%"
set "HTTPS_PROXY=%PIP_PROXY%"

cd /d "%ROOT%"

echo.
echo ========================================
echo   LakeSea Digital Twin - First Setup
echo ========================================
echo   pip proxy: %PIP_PROXY%
echo ========================================
echo.

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

echo [3/4] Seed database...
python -m scripts.seed_db
if errorlevel 1 (
    echo [ERROR] seed_db failed
    popd
    pause
    exit /b 1
)
popd

echo [4/4] Install frontend packages...
pushd "frontend"
if not exist "node_modules" (
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed
        popd
        pause
        exit /b 1
    )
) else (
    echo   node_modules already exists, skip
)
popd

echo.
echo ========================================
echo   Setup done. Run run-all.bat next.
echo ========================================
echo.
pause
