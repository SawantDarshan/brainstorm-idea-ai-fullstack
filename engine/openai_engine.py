# OpenAI engine adapter implementation
from engine.base import BaseEngine
from config.global_context import OPENAI_API_KEY, OPENAI_MODEL

class OpenAIEngine(BaseEngine):
    """OpenAI LLM engine adapter."""

    def __init__(self, model: str = None):
        self.model = model or OPENAI_MODEL

    def create_llm(self, model: str = None, **kwargs):
        """Create an OpenAI ChatModel instance for use in chains."""
        from langchain_openai import ChatOpenAI
        model = model or self.model
        return ChatOpenAI(model=model, api_key=OPENAI_API_KEY, **kwargs)

    def create_agent(self, tools: list = None, model: str = None, **kwargs):
        """Create an OpenAI agent with optional tools."""
        from langchain.agents import create_agent
        model = model or self.model
        return create_agent(model=f"openai:{model}", tools=tools or [], **kwargs)