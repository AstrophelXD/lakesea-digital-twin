@echo off
setlocal EnableExtensions

set "PIP_PROXY=http://127.0.0.1:7897"
set "PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
set "HTTP_PROXY=%PIP_PROXY%"
set "HTTPS_PROXY=%PIP_PROXY%"

cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Run: python -m venv .venv
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat

echo.
echo [1/2] requirements.txt via proxy %PIP_PROXY%
pip install -r requirements.txt --proxy %PIP_PROXY%
if errorlevel 1 (
    echo   Proxy failed, try Tsinghua mirror...
    pip install -r requirements.txt -i %PIP_MIRROR% --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo [ERROR] Failed to install runtime deps
        pause
        exit /b 1
    )
)

echo.
echo [2/2] requirements-dev.txt optional
pip install -r requirements-dev.txt --proxy %PIP_PROXY%
if errorlevel 1 (
    pip install -r requirements-dev.txt -i %PIP_MIRROR% --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo [WARN] pytest not installed, app still runs
    )
)

echo.
echo Done. Run: uvicorn app.main:app --reload
if /i not "%~1"=="--no-pause" pause
