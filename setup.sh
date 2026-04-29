#!/usr/bin/env bash
set -e

echo "============================================"
echo " Multi-Agent Research System - Setup"
echo "============================================"
echo

# Check Python
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] Python3 not found. Install from https://python.org"; exit 1; }

# Check Node
command -v node >/dev/null 2>&1 || { echo "[ERROR] Node.js not found. Install from https://nodejs.org"; exit 1; }

# Install Python deps
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt

# Create .env if missing
if [ ! -f .env ]; then
    echo "[2/4] Creating .env from .env.example..."
    cp .env.example .env
    echo "[!] Edit .env and add your TAVILY_API_KEY"
else
    echo "[2/4] .env already exists, skipping."
fi

# Install frontend deps
echo "[3/4] Installing frontend dependencies..."
npm --prefix frontend install

# Check Ollama
echo "[4/4] Checking Ollama..."
if command -v ollama >/dev/null 2>&1; then
    echo "Pulling model qwen2.5:3b ..."
    ollama pull qwen2.5:3b
else
    echo "[!] Ollama not found. Install from https://ollama.com"
    echo "[!] Then run: ollama pull qwen2.5:3b"
fi

echo
echo "============================================"
echo " Setup complete!"
echo
echo " To start:"
echo "   Terminal 1: python main.py api"
echo "   Terminal 2: npm --prefix frontend run dev"
echo "   Open: http://localhost:3000"
echo "============================================"