import time
import traceback
from interfaces.adapters.base_adapter import BaseAdapter, AdapterRequest, AdapterResponse
from pipelines.research_pipeline import run_pipeline


class ResearchAdapter(BaseAdapter):
    """Concrete adapter that wraps the research pipeline."""

    def execute(self, request: AdapterRequest) -> AdapterResponse:
        start = time.time()
        try:
            state = run_pipeline(request.topic)
            elapsed = round(time.time() - start, 2)
            return AdapterResponse(
                success=True,
                topic=state.topic,
                report=state.report,
                critique=state.critique,
                metadata={
                    "duration_seconds": elapsed,
                    "has_critique": bool(state.critique),
                    "research_length": len(state.research),
                },
            )
        except Exception as exc:
            return AdapterResponse(
                success=False,
                topic=request.topic,
                error=str(exc),
                metadata={"traceback": traceback.format_exc()},
            )