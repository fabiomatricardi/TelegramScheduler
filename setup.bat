@echo off
title TelegramScheduler — Setup
echo ============================================
echo   TelegramScheduler — First-time Setup
echo ============================================
echo.

REM 1. Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] uv not found. Installing...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv. Please install manually:
        echo   https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    echo [OK] uv installed successfully.
) else (
    echo [OK] uv is already installed.
)

echo.
echo [INFO] Installing Python dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

echo.
echo [INFO] Checking telegram_reader configuration...
if not exist "telegram_reader\.env" (
    if exist "telegram_reader\.env.example" (
        echo [INFO] Copying .env.example to .env...
        copy "telegram_reader\.env.example" "telegram_reader\.env" >nul
        echo [WARNING] Please edit telegram_reader\.env with your credentials before running.
    )
) else (
    echo [OK] telegram_reader\.env found.
)

echo.
echo [INFO] Checking opencode CLI...
where opencode >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] opencode CLI is required for LLM features.
    echo   Install: npm install -g opencode-ai
    echo   Then re-run this setup.
    pause
    exit /b 1
) else (
    echo [OK] opencode CLI found.
)

echo.
echo [INFO] Checking opencode-to-openai gateway...
if not exist "opencode-to-openai\index.js" (
    echo [INFO] Gateway not found. Cloning opencode-to-openai...
    where node >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Node.js is required for the LLM gateway.
        echo   Install from: https://nodejs.org/
        echo   Then re-run this setup.
        pause
        exit /b 1
    )
    git clone https://github.com/dxxzst/opencode-to-openai.git opencode-to-openai
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to clone gateway.
        pause
        exit /b 1
    )
    echo [OK] Gateway cloned.
) else (
    echo [OK] Gateway directory found.
)

echo.
echo [INFO] Installing gateway dependencies...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js not found. Skipping npm install.
    echo   Install Node.js from: https://nodejs.org/
    echo   Then run: cd opencode-to-openai ^&^& npm install
) else (
    if not exist "opencode-to-openai\node_modules" (
        pushd opencode-to-openai
        call npm install
        popd
        if %errorlevel% neq 0 (
            echo [ERROR] npm install failed.
            pause
            exit /b 1
        )
        echo [OK] Gateway dependencies installed.
    ) else (
        echo [OK] Gateway dependencies already installed.
    )
)

echo.
echo [INFO] Configuring gateway...
if not exist "opencode-to-openai\config.json" (
    (
        echo {
        echo     "PORT": 8083,
        echo     "API_KEY": "",
        echo     "BIND_HOST": "127.0.0.1",
        echo     "DISABLE_TOOLS": true,
        echo     "OPENCODE_SERVER_URL": "http://127.0.0.1:4097",
        echo     "OPENCODE_PATH": "opencode"
        echo }
    ) > "opencode-to-openai\config.json"
    echo [OK] Created config.json with safe defaults.
    echo   Gateway will auto-detect opencode in PATH.
) else (
    echo [OK] Gateway config.json found.
)

echo.
echo ================================================
echo   Setup complete! Launching TelegramScheduler...
echo ================================================
echo.
uv run python -m scheduler_ui
