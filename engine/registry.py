"""Provider registry - central place for all AI provider configurations."""
import json
import os

DATA_DIR = "/tmp/data" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "data")
SETTINGS_FILE = os.path.join(DATA_DIR, "provider_settings.json")

PROVIDERS = {
    "ollama": {
        "name": "Ollama (Local)",
        "requires_api_key": False,
        "models": ["qwen3.5", "llama3.1", "mistral", "gemma2", "phi3"],
        "description": "Free, local AI models. No API key needed.",
    },
    "openai": {
        "name": "OpenAI",
        "requires_api_key": True,
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "description": "GPT models by OpenAI.",
    },
    "gemini": {
        "name": "Google Gemini",
        "requires_api_key": True,
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
        "description": "Google's Gemini models. Free tier available.",
    },
    "groq": {
        "name": "Groq",
        "requires_api_key": True,
        "models": ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "description": "Ultra-fast inference. Free tier available.",
    },
    "openrouter": {
        "name": "OpenRouter",
        "requires_api_key": True,
        "models": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-flash-1.5", "meta-llama/llama-3.1-8b-instruct"],
        "description": "Access 100+ models with one API key.",
    },
}


def load_settings() -> dict:
    """Load saved provider settings."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"active_provider": "ollama", "active_model": "qwen3.5", "api_keys": {}}


def save_settings(settings: dict):
    """Save provider settings."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def get_engine(provider: str = None, model: str = None, api_key: str = None):
    """Factory: get engine instance for a provider."""
    settings = load_settings()
    provider = provider or settings.get("active_provider", "ollama")
    model = model or settings.get("active_model")
    api_key = api_key or settings.get("api_keys", {}).get(provider, "")

    if provider == "ollama":
        from engine.ollama_engine import OllamaEngine
        return OllamaEngine(model=model)
    elif provider == "openai":
        from engine.openai_engine import OpenAIEngine
        e = OpenAIEngine(model=model)
        if api_key:
            import engine.openai_engine
            # Pass api_key dynamically
            e._api_key = api_key
        return e
    elif provider == "gemini":
        from engine.gemini_engine import GeminiEngine
        return GeminiEngine(model=model, api_key=api_key)
    elif provider == "groq":
        from engine.groq_engine import GroqEngine
        return GroqEngine(model=model, api_key=api_key)
    elif provider == "openrouter":
        from engine.openrouter_engine import OpenRouterEngine
        return OpenRouterEngine(model=model, api_key=api_key)
    else:
        from engine.ollama_engine import OllamaEngine
        return OllamaEngine(model=model)