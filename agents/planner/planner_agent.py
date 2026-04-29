"""Planner Agent - conversational AI that detects intent and dispatches to appropriate agents."""

import json
import re
import uuid
import os
from typing import Generator
from config.global_context import ENGINE_PROVIDER
from pipelines.knowledge_pipeline import KnowledgePipeline


PLANNER_SYSTEM_PROMPT = """You are an AI Canvas Assistant. You help users create knowledge notes, research topics, organize their canvas, and answer questions.

Based on the user's message, you must:
1. Determine the intent
2. Respond conversationally
3. Suggest follow-up actions

## Available Intents:
- "research" — User wants to learn about / research a topic. Extract the topic.
- "create_note" — User wants to create a note or save information. Extract the title and content.
- "organize" — User wants to organize/sort/group their canvas nodes.
- "ask" — User is asking a question about their existing selected documents/nodes.
- "chat" — General conversation, brainstorming, or the user wants your opinion/suggestions.
- "suggest" — User wants suggestions on what to do next or what to explore.

## Context:
- Canvas has {node_count} knowledge nodes.
- Selected nodes: {selected_nodes}
- Conversation so far: {conversation_summary}

## Rules:
- Always respond conversationally and helpfully.
- If intent is "research", you MUST extract the topic to research.
- If intent is "create_note", extract a title and content for the note.
- If intent is "chat", respond directly and offer 2-3 suggestions.
- Return ONLY valid JSON, no markdown fences.

Return format:
{{
  "intent": "research" | "create_note" | "organize" | "ask" | "chat" | "suggest",
  "reply": "Your conversational response to the user...",
  "params": {{
    "topic": "extracted topic (for research)",
    "title": "note title (for create_note)",
    "content": "note content (for create_note)",
    "question": "refined question (for ask)"
  }},
  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
}}

User message: {user_message}
"""


class PlannerAgent:
    """Conversational agent that plans and dispatches actions on the canvas."""

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

    def _get_canvas_context(self) -> dict:
        """Get current canvas state for context."""
        nodes = self.pipeline.get_all_nodes()
        knowledge_nodes = [n for n in nodes if n.get("node_type") != "system" and not n.get("node_id", "").startswith("system-")]
        return {
            "node_count": len(knowledge_nodes),
            "node_names": [n.get("filename", "unknown") for n in knowledge_nodes[:20]],
        }

    def _classify_intent(self, message: str, conversation_history: list, selected_node_ids: list) -> dict:
        """Use LLM to classify user intent and generate response plan."""
        ctx = self._get_canvas_context()

        # Build conversation summary
        conv_summary = ""
        if conversation_history:
            last_3 = conversation_history[-6:]  # last 3 exchanges
            conv_summary = " | ".join([f"{m['role']}: {m['text'][:80]}" for m in last_3])

        selected_info = "None"
        if selected_node_ids:
            nodes = self.pipeline.get_all_nodes()
            sel_nodes = [n for n in nodes if n.get("node_id") in selected_node_ids]
            selected_info = ", ".join([n.get("filename", n.get("node_id", "")) for n in sel_nodes])

        prompt = PLANNER_SYSTEM_PROMPT.format(
            node_count=ctx["node_count"],
            selected_nodes=selected_info,
            conversation_summary=conv_summary or "None",
            user_message=message,
        )

        llm = self.engine.create_llm()
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=prompt), HumanMessage(content=message)]
        response = llm.invoke(messages)

        content = response.content.strip()
        # Parse JSON from response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extracting JSON block
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            # Fallback
            return {
                "intent": "chat",
                "reply": content,
                "params": {},
                "suggestions": ["Research a topic", "Create a new note", "Organize my canvas"],
            }

    def converse(self, message: str, conversation_history: list = None, selected_node_ids: list = None) -> Generator[str, None, None]:
        """
        Main conversational entry point. Yields JSON lines for streaming.
        Each line is a JSON object with type: "thinking" | "reply" | "action" | "nodes_created" | "suggestions" | "done"
        """
        conversation_history = conversation_history or []
        selected_node_ids = selected_node_ids or []

        # Step 1: Classify intent
        yield json.dumps({"type": "thinking", "text": "Understanding your request..."}) + "\n"

        plan = self._classify_intent(message, conversation_history, selected_node_ids)
        intent = plan.get("intent", "chat")
        reply = plan.get("reply", "")
        params = plan.get("params", {})
        suggestions = plan.get("suggestions", [])

        # Step 2: Send initial reply
        yield json.dumps({"type": "reply", "text": reply}) + "\n"

        # Step 3: Execute action based on intent
        if intent == "research":
            topic = params.get("topic", message)
            yield json.dumps({"type": "action", "action": "research", "text": f"🔬 Researching: {topic}..."}) + "\n"
            try:
                from agents.researcher.research_agent import ResearchAgent
                agent = ResearchAgent(self.pipeline)
                result = agent.research(topic)
                node_count = result.get("nodes_created", 0)
                errors = result.get("errors", [])
                yield json.dumps({"type": "nodes_created", "count": node_count, "node_ids": []}) + "\n"
                if errors:
                    yield json.dumps({"type": "error", "text": f"Warnings: {'; '.join(errors)}"}) + "\n"
                yield json.dumps({"type": "reply", "text": f"✅ Created {node_count} research notes on '{topic}'. Reload to see them."}) + "\n"
                if node_count > 0:
                    yield json.dumps({"type": "action", "action": "reload", "text": "Reloading canvas..."}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "text": f"Research failed: {str(e)}"}) + "\n"

        elif intent == "create_note":
            title = params.get("title", f"📝 {message[:30]}")
            content = params.get("content", message)
            yield json.dumps({"type": "action", "action": "create_note", "text": f"📝 Creating note: {title}"}) + "\n"
            try:
                node_id = str(uuid.uuid4())
                filepath = os.path.join(self.pipeline.data_dir, f"{node_id}.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                meta = {
                    "node_id": node_id,
                    "filename": title,
                    "characters": len(content),
                    "x": 10200,
                    "y": 10200,
                    "parent_id": None,
                    "node_type": "knowledge",
                }
                self.pipeline._add_node_meta(meta)
                yield json.dumps({"type": "nodes_created", "count": 1, "node_ids": [node_id], "nodes": [meta]}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "text": f"Failed to create note: {str(e)}"}) + "\n"

        elif intent == "organize":
            yield json.dumps({"type": "action", "action": "organize", "text": "✨ Organizing your canvas..."}) + "\n"
            try:
                from agents.organizer.organizer_agent import OrganizerAgent
                agent = OrganizerAgent(self.pipeline)
                result = agent.organize(pattern="categories")
                results = result.get("results", {})
                yield json.dumps({"type": "reply", "text": f"✅ Organized! Created {results.get('groups_created', 0)} groups, {results.get('nodes_created', 0)} summary nodes."}) + "\n"
                yield json.dumps({"type": "action", "action": "reload", "text": "Reloading canvas..."}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "text": f"Organize failed: {str(e)}"}) + "\n"

        elif intent == "ask" and selected_node_ids:
            question = params.get("question", message)
            yield json.dumps({"type": "action", "action": "ask", "text": f"💡 Analyzing selected documents..."}) + "\n"
            try:
                from agents.support.support_agent import SupportAgent
                agent = SupportAgent(self.pipeline)
                answer = ""
                for chunk in agent.ask_stream(selected_node_ids, question):
                    answer += chunk
                yield json.dumps({"type": "reply", "text": answer}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "text": f"Ask failed: {str(e)}"}) + "\n"

        elif intent == "suggest":
            # Suggestions already in plan, just reinforce
            ctx = self._get_canvas_context()
            if ctx["node_count"] == 0:
                suggestions = ["Research a topic to get started", "Create a note with your ideas", "Upload a PDF document"]
            elif ctx["node_count"] < 5:
                suggestions = ["Research more about your topics", "Organize your canvas", "Ask a question about your notes"]

        # Step 4: Send suggestions
        if suggestions:
            yield json.dumps({"type": "suggestions", "suggestions": suggestions}) + "\n"

        yield json.dumps({"type": "done"}) + "\n"