@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set SKILL_DIR=%~dp0
set VENV_DIR=%SKILL_DIR%.venv

echo ============================================================
echo   nacos-config skill — Setup
echo ============================================================
echo.

REM === 1. Python ===
echo [1/3] Checking Python...
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do set PY_VER=%%v
    for /f "tokens=1,2 delims=." %%a in ("!PY_VER!") do (
        if %%a geq 3 if %%b geq 8 ( set PYTHON_CMD=python & echo [OK] Python !PY_VER! & goto :python_ok )
    )
)
echo [ERROR] Python 3.8+ not found. Install from https://www.python.org/downloads/
exit /b 1
:python_ok

REM === 2. Virtual environment + deps ===
echo.
echo [2/3] Setting up virtual environment...
if not exist "%VENV_DIR%" (
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

call "%VENV_DIR%\Scripts\activate.bat"
pip install -r "%SKILL_DIR%requirements.txt" -q 2>nul
if %errorlevel% neq 0 (
    echo [!] PyPI failed, trying Tsinghua mirror...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r "%SKILL_DIR%requirements.txt" -q
    if !errorlevel! neq 0 ( echo [ERROR] Dependency install failed & exit /b 1 )
)
echo [OK] Dependencies installed

REM === 3. Config ===
echo.
echo [3/3] Checking config.ini...
if exist "%SKILL_DIR%config.ini" (
    echo [OK] config.ini found
) else (
    copy "%SKILL_DIR%config.ini.example" "%SKILL_DIR%config.ini" >nul
    echo [!] config.ini created from template.
    echo     Edit %SKILL_DIR%config.ini with real credentials before use.
)

echo.
echo ============================================================
echo [OK] Setup complete
echo.
echo Usage:
echo   python "%SKILL_DIR%nacos_config.py" fetch --env local
echo   python "%SKILL_DIR%nacos_config.py" push --env local --file path/to/nacos.yaml
echo   python "%SKILL_DIR%nacos_config.py" diff --env local
echo ============================================================
endlocal
