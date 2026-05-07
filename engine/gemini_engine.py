"""Google Gemini engine adapter."""
from engine.base import BaseEngine


class GeminiEngine(BaseEngine):
    """Google Gemini LLM engine adapter."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or "gemini-1.5-flash"
        self.api_key = api_key

    def create_llm(self, model: str = None, **kwargs):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = model or self.model
        return ChatGoogleGenerativeAI(model=model, google_api_key=self.api_key, **kwargs)

    def create_agent(self, tools: list = None, model: str = None, **kwargs):
        from langgraph.prebuilt import create_react_agent
        llm = self.create_llm(model=model)
        return create_react_agent(llm, tools=tools or [])