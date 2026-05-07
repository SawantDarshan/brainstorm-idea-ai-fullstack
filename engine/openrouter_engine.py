"""OpenRouter engine adapter - access 100+ models via one API key."""
from engine.base import BaseEngine

class OpenRouterEngine(BaseEngine):
    """OpenRouter LLM engine adapter (OpenAI-compatible)."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or "openai/gpt-4o-mini"
        self.api_key = api_key

    def create_llm(self, model: str = None, **kwargs):
        from langchain_openai import ChatOpenAI
        model = model or self.model
        return ChatOpenAI(
            model=model,
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            **kwargs,
        )

    def create_agent(self, tools: list = None, model: str = None, **kwargs):
        from langgraph.prebuilt import create_react_agent
        llm = self.create_llm(model=model)
        return create_react_agent(llm, tools=tools or [])