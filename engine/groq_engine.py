"""Groq engine adapter."""
from engine.base import BaseEngine

class GroqEngine(BaseEngine):
    """Groq LLM engine adapter (fast inference)."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or "llama-3.1-8b-instant"
        self.api_key = api_key

    def create_llm(self, model: str = None, **kwargs):
        from langchain_groq import ChatGroq
        model = model or self.model
        return ChatGroq(model=model, groq_api_key=self.api_key, **kwargs)

    def create_agent(self, tools: list = None, model: str = None, **kwargs):
        from langgraph.prebuilt import create_react_agent
        llm = self.create_llm(model=model)
        return create_react_agent(llm, tools=tools or [])