"""Organizer Agent - uses AI to classify, group, and structure canvas nodes."""

import json
import re
import uuid
from config.global_context import ENGINE_PROVIDER
from pipelines.knowledge_pipeline import KnowledgePipeline

PATTERN_PROMPTS = {
    "mindmap": """Organize these nodes as a MIND MAP: pick the most central/overview node as the root, then create parent-child relationships radiating outward by topic. Group tightly related nodes. Create summary nodes as needed to serve as branch headers. The result should form a tree structure.""",
    "categories": """Organize these nodes into CATEGORY GROUPS: cluster nodes by topic/theme. Each group should have a descriptive name. Create a NEW summary node for each category that provides an overview. Remove duplicates.""",
    "dependencies": """Organize these nodes by DEPENDENCIES/RELATIONSHIPS: identify which documents reference, depend on, or extend other documents. Create parent-child relationships where a parent document is foundational and children build on it. Create overview nodes where needed.""",
    "timeline": """Organize these nodes in a TIMELINE/SEQUENCE: if documents have dates or sequential topics, arrange them as parent-child chains in chronological or logical order. Group related sequences. Create timeline header nodes.""",
}

ORGANIZER_PROMPT = """You are a Canvas Organizer AI. You will be given a list of document nodes from a knowledge canvas. Each node has an id, filename, and a preview of its content.

ORGANIZATION PATTERN: {pattern_instruction}

Your job is to analyze ALL nodes and return a JSON plan to organize them:

1. **groups**: Group related nodes together by topic/category. Each group has a name and list of node_ids.
2. **parent_child**: Suggest hierarchical relationships where one document is clearly a parent/overview and others are sub-topics or details.
3. **duplicates**: Identify nodes with duplicate or near-identical content. For each set, pick one to keep and list others to remove.
4. **create_nodes**: Create NEW summary/overview nodes that consolidate or summarize related content. These become parent nodes for their children.

Rules:
- System nodes (ids starting with "system-") must be EXCLUDED from all operations.
- Conversation nodes (node_type "conversation") should be EXCLUDED.
- Only organize knowledge/document nodes.
- A node can only be in ONE group.
- A node can only have ONE parent.
- You SHOULD create new summary nodes to act as category headers or to consolidate information.
- Return ONLY valid JSON, no markdown, no explanation.

Return format:
{{
  "groups": [
    {{"group_name": "Topic Name", "node_ids": ["id1", "id2"]}}
  ],
  "parent_child": [
    {{"parent_id": "id1", "child_id": "id2"}}
  ],
  "duplicates": [
    {{"keep_id": "id1", "remove_ids": ["id2", "id3"]}}
  ],
  "create_nodes": [
    {{"filename": "Summary Title", "content": "A brief overview/summary text...", "child_ids": ["id1", "id2"]}}
  ]
}}

If no action is needed for a category, return an empty array.

Here are the nodes:
{nodes_info}
"""


class OrganizerAgent:
    """Agent that analyzes all canvas nodes and suggests/applies organization."""

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

    def _gather_nodes_info(self) -> tuple[list[dict], str]:
        """Gather all organizable nodes with content previews."""
        all_nodes = self.pipeline.get_all_nodes()
        organizable = []
        for n in all_nodes:
            nid = n.get("node_id", "")
            if nid.startswith("system-"):
                continue
            if n.get("node_type") == "conversation":
                continue
            preview = ""
            try:
                text = self.pipeline.load_knowledge(nid)
                preview = text[:500].replace("\n", " ").strip()
            except FileNotFoundError:
                preview = "[no content]"
            organizable.append({
                "node_id": nid,
                "filename": n.get("filename", "unknown"),
                "characters": n.get("characters", 0),
                "preview": preview,
            })
        info_text = json.dumps(organizable, indent=2)
        return organizable, info_text

    @staticmethod
    def _parse_json_safe(text: str) -> dict:
        """Robustly parse JSON from LLM output, handling common issues."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting the outermost { ... } block
        depth = 0
        start = None
        for i, ch in enumerate(text):
            if ch == '{':
                if start is None:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    block = text[start:i + 1]
                    try:
                        return json.loads(block)
                    except json.JSONDecodeError:
                        # Try fixing common issues: trailing commas, single quotes
                        cleaned = re.sub(r',\s*([}\]])', r'\1', block)  # remove trailing commas
                        try:
                            return json.loads(cleaned)
                        except json.JSONDecodeError:
                            pass
                    start = None

        # Last resort: return empty plan
        return {"groups": [], "parent_child": [], "duplicates": [], "create_nodes": []}

    def _clear_existing_organization(self):
        """Remove all existing groups and non-system parent-child relationships."""
        nodes = self.pipeline.get_all_nodes()
        for n in nodes:
            nid = n.get("node_id", "")
            if nid.startswith("system-"):
                continue
            if n.get("node_type") == "conversation":
                continue
            # Clear group
            if n.get("group_id"):
                try:
                    self.pipeline.ungroup_node(nid)
                except Exception:
                    pass
            # Clear parent-child (only if parent is non-system)
            if n.get("parent_id") and not n["parent_id"].startswith("system-"):
                try:
                    self.pipeline.disconnect_nodes(n["parent_id"], nid)
                except Exception:
                    pass

    def get_plan(self, pattern: str = "categories", custom_instruction: str = "") -> dict:
        """Ask LLM to analyze nodes and return an organization plan."""
        organizable, info_text = self._gather_nodes_info()
        if len(organizable) < 2:
            return {"groups": [], "parent_child": [], "duplicates": [], "create_nodes": [], "message": "Not enough nodes to organize."}

        pattern_instruction = PATTERN_PROMPTS.get(pattern, "")
        if pattern == "custom" and custom_instruction:
            pattern_instruction = custom_instruction
        elif not pattern_instruction:
            pattern_instruction = PATTERN_PROMPTS["categories"]

        llm = self.engine.create_llm()
        prompt = ORGANIZER_PROMPT.format(pattern_instruction=pattern_instruction, nodes_info=info_text)
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=prompt), HumanMessage(content="Analyze these nodes and return the organization plan as JSON.")]
        response = llm.invoke(messages)

        content = response.content.strip()
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            content = json_match.group(1).strip()

        plan = self._parse_json_safe(content)

        plan.setdefault("groups", [])
        plan.setdefault("parent_child", [])
        plan.setdefault("duplicates", [])
        plan.setdefault("create_nodes", [])
        return plan

    def apply_plan(self, plan: dict) -> dict:
        """Apply the organization plan to the canvas."""
        results = {"groups_created": 0, "connections_made": 0, "duplicates_removed": 0, "nodes_created": 0, "errors": []}

        # 1. Create new summary nodes
        created_id_map = {}  # temp reference for parent_child
        for cn in plan.get("create_nodes", []):
            try:
                filename = cn.get("filename", "📋 Summary")
                content = cn.get("content", "")
                node_id = str(uuid.uuid4())
                # Save knowledge text
                import os
                filepath = os.path.join(self.pipeline.data_dir, f"{node_id}.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                # Add node meta
                meta = {
                    "node_id": node_id,
                    "filename": filename,
                    "characters": len(content),
                    "x": 100,
                    "y": 100,
                    "parent_id": None,
                    "children": [],
                    "node_type": "knowledge",
                }
                self.pipeline._add_node_meta(meta)
                created_id_map[filename] = node_id
                # Set children
                for cid in cn.get("child_ids", []):
                    try:
                        self.pipeline.connect_nodes(node_id, cid, "parent")
                        results["connections_made"] += 1
                    except Exception as e:
                        results["errors"].append(f"Child connect: {str(e)}")
                results["nodes_created"] += 1
            except Exception as e:
                results["errors"].append(f"Create node error: {str(e)}")

        # 2. Apply groups
        for group in plan.get("groups", []):
            ids = group.get("node_ids", [])
            if len(ids) < 2:
                continue
            try:
                self.pipeline.connect_nodes(ids[0], ids[1], "group")
                for i in range(2, len(ids)):
                    self.pipeline.connect_nodes(ids[0], ids[i], "group")
                results["groups_created"] += 1
            except Exception as e:
                results["errors"].append(f"Group error: {str(e)}")

        # 3. Apply parent-child
        for pc in plan.get("parent_child", []):
            pid = pc.get("parent_id")
            cid = pc.get("child_id")
            if not pid or not cid:
                continue
            # Resolve created node references
            if pid in created_id_map:
                pid = created_id_map[pid]
            if cid in created_id_map:
                cid = created_id_map[cid]
            try:
                self.pipeline.connect_nodes(pid, cid, "parent")
                results["connections_made"] += 1
            except Exception as e:
                results["errors"].append(f"Parent-child error: {str(e)}")

        # 4. Remove duplicates
        for dup in plan.get("duplicates", []):
            for rid in dup.get("remove_ids", []):
                try:
                    self.pipeline.delete_node(rid)
                    results["duplicates_removed"] += 1
                except Exception as e:
                    results["errors"].append(f"Delete error: {str(e)}")

        return results

    def _reposition_all_nodes(self, pattern: str):
        """Reposition ALL organizable nodes into a layout pattern."""
        all_nodes = self.pipeline.get_all_nodes()
        organizable = [n for n in all_nodes
                       if not n.get("node_id", "").startswith("system-")
                       and n.get("node_type") != "conversation"]

        if not organizable:
            return

        start_x, start_y = 10100, 10100
        spacing_x, spacing_y = 280, 120

        if pattern == "mindmap":
            # Build tree from parent_child relationships
            children_map = {}
            has_parent = set()
            for n in organizable:
                pid = n.get("parent_id")
                if pid and not pid.startswith("system-"):
                    children_map.setdefault(pid, []).append(n["node_id"])
                    has_parent.add(n["node_id"])
            roots = [n["node_id"] for n in organizable if n["node_id"] not in has_parent]
            if not roots:
                roots = [organizable[0]["node_id"]]

            placed = set()
            def place_tree(nid, px, py):
                if nid in placed:
                    return py
                placed.add(nid)
                self.pipeline.update_node_position(nid, px, py)
                kids = children_map.get(nid, [])
                child_y = py
                for kid in kids:
                    child_y = place_tree(kid, px + spacing_x, child_y)
                    child_y += spacing_y
                return max(py + spacing_y, child_y)

            cy = start_y
            for root in roots:
                cy = place_tree(root, start_x, cy)
            for n in organizable:
                if n["node_id"] not in placed:
                    self.pipeline.update_node_position(n["node_id"], start_x, cy)
                    cy += spacing_y

        elif pattern == "categories":
            # Group nodes by group_id, then lay out in grid clusters
            refreshed = self.pipeline.get_all_nodes()
            org_map = {n["node_id"]: n for n in refreshed if not n.get("node_id", "").startswith("system-") and n.get("node_type") != "conversation"}
            groups = {}
            ungrouped = []
            for nid, n in org_map.items():
                gid = n.get("group_id")
                if gid:
                    groups.setdefault(gid, []).append(nid)
                else:
                    ungrouped.append(nid)

            gy = start_y
            for gid, ids in groups.items():
                for i, nid in enumerate(ids):
                    self.pipeline.update_node_position(nid, start_x + (i % 3) * spacing_x, gy + (i // 3) * spacing_y)
                gy += ((len(ids) // 3) + 1) * spacing_y + 80

            for i, nid in enumerate(ungrouped):
                self.pipeline.update_node_position(nid, start_x + (i % 4) * spacing_x, gy + (i // 4) * spacing_y)

        elif pattern in ("dependencies", "timeline"):
            # Chain layout
            x, y = start_x, start_y
            for i, n in enumerate(organizable):
                self.pipeline.update_node_position(n["node_id"], x, y)
                x += spacing_x
                if x > start_x + spacing_x * 4:
                    x = start_x
                    y += spacing_y

        else:
            # Simple grid for custom
            for i, n in enumerate(organizable):
                self.pipeline.update_node_position(n["node_id"], start_x + (i % 4) * spacing_x, start_y + (i // 4) * spacing_y)

    def organize(self, pattern: str = "categories", custom_instruction: str = "") -> dict:
        """Full pipeline: clear old org, get plan from LLM, apply it, reposition."""
        # Clear existing organization first
        self._clear_existing_organization()

        plan = self.get_plan(pattern=pattern, custom_instruction=custom_instruction)
        if plan.get("message"):
            return {"plan": plan, "results": None}

        results = self.apply_plan(plan)
        self._reposition_all_nodes(pattern)
        return {"plan": plan, "results": results}