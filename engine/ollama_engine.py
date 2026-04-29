# Ollama engine adapter implementation
from engine.base import BaseEngine
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from config.global_context import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, OLLAMA_HOST


class OllamaEngine(BaseEngine):
    """Ollama LLM engine adapter."""

    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL

    def create_llm(self, model: str = None, **kwargs):
        """Create an Ollama ChatModel instance for use in chains."""
        model = model or self.model
        defaults = {
            "base_url": OLLAMA_HOST,
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": DEFAULT_MAX_TOKENS,
        }
        defaults.update(kwargs)
        return ChatOllama(model=model, **defaults)

    def create_agent(self, tools: list = None, model: str = None, **kwargs):
        """Create a ReAct agent with optional tools."""
        llm = self.create_llm(model=model)
        return create_react_agent(llm, tools=tools or [])
