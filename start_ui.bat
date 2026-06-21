@echo off
title TelegramScheduler
REM 1. Check if uv is available
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv not found. Run setup.bat first.
    pause
    exit /b 1
)

REM 2. Check if .venv exists (dependencies installed)
if not exist ".venv" (
    echo ERROR: Dependencies not installed. Run setup.bat first.
    pause
    exit /b 1
)

REM 3. Check if telegram_reader .env exists
if not exist "telegram_reader\.env" (
    echo WARNING: telegram_reader\.env not found.
    echo Copying .env.example to .env...
    if exist "telegram_reader\.env.example" (
        copy "telegram_reader\.env.example" "telegram_reader\.env" >nul
        echo Please edit telegram_reader\.env with your credentials before running.
        pause
        exit /b 1
    ) else (
        echo ERROR: No .env.example found. Please create telegram_reader\.env manually.
        pause
        exit /b 1
    )
)

REM 4. Launch Flask GUI
uv run python -m scheduler_ui
