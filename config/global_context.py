# Global context and shared settings - all configurable via env variables
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# ENGINE SETTINGS
# =============================================================================
# ENGINE_PROVIDER: "ollama" | "openai" (determines which engine adapter to use)
ENGINE_PROVIDER = os.getenv("ENGINE_PROVIDER", "ollama")

# Model name (format depends on provider)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# =============================================================================
# API KEYS
# =============================================================================
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# =============================================================================
# SEARCH SETTINGS
# =============================================================================
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "tavily")  # "tavily" | future providers
SEARCH_NUM_RESULTS = int(os.getenv("SEARCH_NUM_RESULTS", "5"))

# =============================================================================
# SCRAPER SETTINGS
# =============================================================================
SCRAPE_MAX_CHARS = int(os.getenv("SCRAPE_MAX_CHARS", "3000"))
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "10"))

# =============================================================================
# INTERFACE SETTINGS
# =============================================================================
# APP_MODE: "cli" | "api" | "web"
APP_MODE = os.getenv("APP_MODE", "cli")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# =============================================================================
# FEATURE FLAGS
# =============================================================================
ENABLE_CRITIQUE = os.getenv("ENABLE_CRITIQUE", "true").lower() == "true"
ENABLE_SCRAPING = os.getenv("ENABLE_SCRAPING", "true").lower() == "true"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# =============================================================================
# GLOBAL CONTEXT (consolidated)
# =============================================================================
GLOBAL_CONTEXT = {
    "project_name": "multi-agent-system",
    "engine_provider": ENGINE_PROVIDER,
    "default_model": DEFAULT_MODEL,
    "temperature": DEFAULT_TEMPERATURE,
    "max_tokens": DEFAULT_MAX_TOKENS,
    "search_provider": SEARCH_PROVIDER,
    "enable_critique": ENABLE_CRITIQUE,
    "enable_scraping": ENABLE_SCRAPING,
    "debug": DEBUG,
}