@echo off
echo ============================================
echo  Brainstorm Idea AI - Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    exit /b 1
)

:: Install Python deps
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt

:: Create .env if missing
if not exist .env (
    echo [2/3] Creating .env file...
    (
        echo # Add your API keys here
        echo OPENAI_API_KEY=
        echo TAVILY_API_KEY=
        echo APP_MODE=web
    ) > .env
    echo [!] Edit .env and add your API keys
) else (
    echo [2/3] .env already exists, skipping.
)

:: Check Ollama
echo [3/3] Checking Ollama (optional)...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [!] Ollama not found (optional). Install from https://ollama.com
) else (
    echo Pulling model qwen2.5:3b ...
    ollama pull qwen2.5:3b
)

echo.
echo ============================================
echo  Setup complete!
echo.
echo  To run the project:
echo    python main.py web    (web interface)
echo    python main.py api    (API server)
echo    python main.py cli    (CLI mode)
echo ============================================