@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
cd /d "%ROOT%backend"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] backend\.venv not found. Run setup.bat first.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   LakeSea - Reset Demo Database Only
echo   For full pre-defense: pre-defense.bat
echo ========================================
echo.

call .venv\Scripts\activate.bat
python -m scripts.reset_demo_db --full
if errorlevel 1 (
    echo [ERROR] reset failed
    pause
    exit /b 1
)

echo.
echo Done. Run pre-defense.bat to reset and start services.
echo.
pause
