# Abstract base engine interface - adapter pattern
from abc import ABC, abstractmethod


class BaseEngine(ABC):
    """Abstract base class for LLM engine adapters.
    Implement this interface to add support for new LLM providers.
    """

    @abstractmethod
    def create_llm(self, model: str = None, **kwargs):
        """Create and return an LLM instance."""
        pass

    @abstractmethod
    def create_agent(self, tools: list = None, model: str = None, **kwargs):
        """Create and return an agent with optional tools."""
        pass