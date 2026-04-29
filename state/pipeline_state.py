# Pipeline state management
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PipelineState:
    """Centralized state for pipeline execution."""
    topic: str = ""
    research: str = ""
    scraped_content: str = ""
    report: str = ""
    critique: str = ""
    metadata: dict = field(default_factory=dict)

    def get_combined_research(self) -> str:
        return self.research + "\n\n" + self.scraped_content