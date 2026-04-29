# Base guardrail interface
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class GuardResult:
    """Result of a guardrail check."""
    passed: bool
    message: str = ""
    sanitized_content: Optional[str] = None

class BaseGuard(ABC):
    """Abstract base class for guardrails."""

    @abstractmethod
    def check(self, content: str, **kwargs) -> GuardResult:
        """Check content against this guardrail. Return GuardResult."""
        pass