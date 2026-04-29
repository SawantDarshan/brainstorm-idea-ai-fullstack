# Engine factory - selects engine adapter based on env config
from config.global_context import ENGINE_PROVIDER

def get_engine():
    """Get the configured engine adapter based on ENGINE_PROVIDER env var."""
    if ENGINE_PROVIDER == "ollama":
        from engine.ollama_engine import OllamaEngine
        return OllamaEngine()
    elif ENGINE_PROVIDER == "openai":
        from engine.openai_engine import OpenAIEngine
        return OpenAIEngine()
    else:
        raise ValueError(f"Unknown ENGINE_PROVIDER: {ENGINE_PROVIDER}. Use 'ollama' or 'openai'.")

# Default engine instance
default_engine = get_engine()