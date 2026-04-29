#!/usr/bin/env bash
set -e

echo "============================================"
echo " Brainstorm Idea AI - Setup & Run"
echo "============================================"
echo

# Check Python
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] Python3 not found. Install from https://python.org"; exit 1; }

# Install Python deps
echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt

# Create .env if missing
if [ ! -f .env ]; then
    echo "[2/3] Creating .env file..."
    cat > .env <<EOF
# Add your API keys here
OPENAI_API_KEY=
TAVILY_API_KEY=
APP_MODE=web
EOF
    echo "[!] Edit .env and add your API keys"
else
    echo "[2/3] .env already exists, skipping."
fi

# Check Ollama (optional)
echo "[3/3] Checking Ollama (optional)..."
if command -v ollama >/dev/null 2>&1; then
    echo "Pulling model qwen2.5:3b ..."
    ollama pull qwen2.5:3b
else
    echo "[!] Ollama not found (optional). Install from https://ollama.com"
fi

echo
echo "============================================"
echo " Setup complete!"
echo
echo " To run the project:"
echo "   python main.py web    (web interface)"
echo "   python main.py api    (API server)"
echo "   python main.py cli    (CLI mode)"
echo "============================================"