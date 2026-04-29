"""Support Agent - answers questions using knowledge from selected nodes."""

from config.global_context import ENGINE_PROVIDER
from pipelines.knowledge_pipeline import KnowledgePipeline


SYSTEM_PROMPT = """You are a helpful Support Agent. Answer the user's question based ONLY on the provided context documents. If the context doesn't contain enough information to answer, say so clearly. Be concise and accurate.

Context Documents:
{context}
"""


class SupportAgent:
    """Agent that answers questions using knowledge from canvas nodes."""

    def __init__(self, knowledge_pipeline: KnowledgePipeline = None):
        self.pipeline = knowledge_pipeline or KnowledgePipeline()
        self.engine = self._create_engine()

    def _create_engine(self):
        if ENGINE_PROVIDER == "openai":
            from engine.openai_engine import OpenAIEngine
            return OpenAIEngine()
        else:
            from engine.ollama_engine import OllamaEngine
            return OllamaEngine()

    def gather_context(self, node_ids: list[str]) -> str:
        """Load and concatenate knowledge text from given node IDs."""
        texts = []
        for nid in node_ids:
            try:
                text = self.pipeline.load_knowledge(nid)
                nodes = self.pipeline.get_all_nodes()
                node = next((n for n in nodes if n["node_id"] == nid), None)
                name = node["filename"] if node else nid
                texts.append(f"--- {name} ---\n{text}\n")
            except FileNotFoundError:
                texts.append(f"--- {nid} ---\n[Knowledge not found]\n")
        return "\n".join(texts)

    def ask(self, node_ids: list[str], question: str) -> str:
        """Ask a question with context from the given nodes. Returns full answer."""
        context = self.gather_context(node_ids)
        llm = self.engine.create_llm()
        prompt = SYSTEM_PROMPT.format(context=context)
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=prompt), HumanMessage(content=question)]
        response = llm.invoke(messages)
        return response.content

    def ask_stream(self, node_ids: list[str], question: str):
        """Ask a question and yield streamed chunks."""
        context = self.gather_context(node_ids)
        llm = self.engine.create_llm()
        prompt = SYSTEM_PROMPT.format(context=context)
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=prompt), HumanMessage(content=question)]
        for chunk in llm.stream(messages):
            if chunk.content:
                yield chunk.content