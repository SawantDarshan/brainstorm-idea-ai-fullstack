from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AdapterRequest:
    """Standardized input for all adapters."""
    topic: str
    options: dict = field(default_factory=dict)


@dataclass
class AdapterResponse:
    """Standardized output from all adapters."""
    success: bool
    topic: str
    report: str = ""
    critique: str = ""
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


class BaseAdapter(ABC):
    """Abstract adapter interface – every pipeline adapter must implement execute()."""

    @abstractmethod
    def execute(self, request: AdapterRequest) -> AdapterResponse:
        ...