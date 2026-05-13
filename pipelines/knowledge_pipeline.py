"""Knowledge pipeline - extracts text from uploaded files and stores as knowledge."""

import os
import uuid
import io
import json
from PyPDF2 import PdfReader


class KnowledgePipeline:
    """Pipeline for converting uploaded files into knowledge (text)."""

    # Fixed system node IDs
    SYSTEM_CHAT_ID = "system-chat"
    SYSTEM_VOICE_ID = "system-voice"
    SYSTEM_AGENT_ID = "system-agent"
    SYSTEM_ORGANIZER_ID = "system-organizer"
    SYSTEM_RESEARCHER_ID = "system-researcher"

    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = data_dir
        elif os.environ.get("VERCEL"):
            self.data_dir = "/tmp/data"
        else:
            self.data_dir = os.path.join(
                os.path.dirname(__file__), "..", "data"
            )
        os.makedirs(self.data_dir, exist_ok=True)
        self._files_dir = os.path.join(self.data_dir, "files")
        os.makedirs(self._files_dir, exist_ok=True)
        self._nodes_file = os.path.join(self.data_dir, "nodes.json")
        if not os.path.exists(self._nodes_file):
            self._save_nodes([])
        self._ensure_system_nodes()

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extract text from file bytes based on file type."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return self._extract_pdf(file_bytes)
        raise ValueError(f"Unsupported file type: {ext}")

    def _extract_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

    def save_knowledge(self, text: str) -> str:
        """Save extracted text to data folder. Returns node_id."""
        node_id = str(uuid.uuid4())
        filepath = os.path.join(self.data_dir, f"{node_id}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return node_id

    def load_knowledge(self, node_id: str) -> str:
        """Load knowledge text by node_id."""
        filepath = os.path.join(self.data_dir, f"{node_id}.txt")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Knowledge not found for node: {node_id}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def _save_original_file(self, node_id: str, file_bytes: bytes, filename: str):
        """Save the original uploaded file to data/files/."""
        ext = os.path.splitext(filename)[1].lower()
        filepath = os.path.join(self._files_dir, f"{node_id}{ext}")
        with open(filepath, "wb") as f:
            f.write(file_bytes)

    def process(self, file_bytes: bytes, filename: str, x: float = 0, y: float = 0) -> dict:
        """Full pipeline: extract text from file and save as knowledge."""
        text = self.extract_text(file_bytes, filename)
        if not text.strip():
            raise ValueError("Could not extract any text from the file.")
        node_id = self.save_knowledge(text)
        self._save_original_file(node_id, file_bytes, filename)
        meta = {
            "node_id": node_id,
            "filename": filename,
            "characters": len(text),
            "x": x,
            "y": y,
        }
        self._add_node_meta(meta)
        return meta

    # ── System nodes ──

    def _ensure_system_nodes(self):
        """Ensure system nodes (chat, voice) exist in nodes.json."""
        nodes = self._load_nodes()
        ids = {n["node_id"] for n in nodes}
        changed = False
        if self.SYSTEM_CHAT_ID not in ids:
            nodes.append({
                "node_id": self.SYSTEM_CHAT_ID,
                "filename": "💬 Chat Input",
                "node_type": "system",
                "parent_id": None,
                "children": [],
                "characters": 0,
                "x": 10040, "y": 10500,
            })
            changed = True
        if self.SYSTEM_VOICE_ID not in ids:
            nodes.append({
                "node_id": self.SYSTEM_VOICE_ID,
                "filename": "🎤 Voice Mode",
                "node_type": "system",
                "parent_id": None,
                "children": [],
                "characters": 0,
                "x": 10340, "y": 10500,
            })
            changed = True
        if self.SYSTEM_AGENT_ID not in ids:
            nodes.append({
                "node_id": self.SYSTEM_AGENT_ID,
                "filename": "🤖 Support Agent",
                "node_type": "system",
                "parent_id": None,
                "children": [],
                "characters": 0,
                "x": 10640, "y": 10500,
            })
            changed = True
        if self.SYSTEM_ORGANIZER_ID not in ids:
            nodes.append({
                "node_id": self.SYSTEM_ORGANIZER_ID,
                "filename": "🧠 Organizer Agent",
                "node_type": "system",
                "parent_id": None,
                "children": [],
                "characters": 0,
                "x": 10940, "y": 10500,
            })
            changed = True
        if self.SYSTEM_RESEARCHER_ID not in ids:
            nodes.append({
                "node_id": self.SYSTEM_RESEARCHER_ID,
                "filename": "🔬 Research Agent",
                "node_type": "system",
                "parent_id": None,
                "children": [],
                "characters": 0,
                "x": 11240, "y": 10500,
            })
            changed = True
        if changed:
            self._save_nodes(nodes)

    # ── Node metadata persistence ──

    def _load_nodes(self) -> list:
        try:
            with open(self._nodes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_nodes(self, nodes: list):
        with open(self._nodes_file, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2)

    def _add_node_meta(self, meta: dict):
        """Add node metadata. If parent_id is set, also update parent's children list."""
        # Ensure defaults for tree fields
        meta.setdefault("parent_id", None)
        meta.setdefault("children", [])
        meta.setdefault("node_type", "knowledge")
        nodes = self._load_nodes()
        # Update parent's children array
        if meta.get("parent_id"):
            for n in nodes:
                if n["node_id"] == meta["parent_id"]:
                    if "children" not in n:
                        n["children"] = []
                    n["children"].append(meta["node_id"])
                    break
        nodes.append(meta)
        self._save_nodes(nodes)

    def get_all_nodes(self) -> list:
        """Return all node metadata."""
        return self._load_nodes()

    def delete_node(self, node_id: str):
        """Delete node metadata, knowledge file, original file, and remove from parent's children."""
        nodes = self._load_nodes()
        # Find the node to get its parent
        target = next((n for n in nodes if n["node_id"] == node_id), None)
        if target and target.get("parent_id"):
            for n in nodes:
                if n["node_id"] == target["parent_id"] and "children" in n:
                    n["children"] = [c for c in n["children"] if c != node_id]
                    break
        # Also delete all children recursively
        children_to_delete = set()
        if target and target.get("children"):
            children_to_delete = set(target["children"])
        nodes = [n for n in nodes if n["node_id"] != node_id and n["node_id"] not in children_to_delete]
        self._save_nodes(nodes)
        # Remove knowledge text
        filepath = os.path.join(self.data_dir, f"{node_id}.txt")
        if os.path.exists(filepath):
            os.remove(filepath)
        # Remove original file (any extension)
        import glob
        for f in glob.glob(os.path.join(self._files_dir, f"{node_id}.*")):
            os.remove(f)

    def update_node_position(self, node_id: str, x: float, y: float):
        """Update node position in metadata."""
        nodes = self._load_nodes()
        for n in nodes:
            if n["node_id"] == node_id:
                n["x"] = x
                n["y"] = y
                break
        self._save_nodes(nodes)

    def connect_nodes(self, source_id: str, target_id: str, action: str):
        """Connect two nodes: action is 'parent', 'child', or 'group'."""
        nodes = self._load_nodes()
        source = next((n for n in nodes if n["node_id"] == source_id), None)
        target = next((n for n in nodes if n["node_id"] == target_id), None)
        if not source or not target:
            raise FileNotFoundError("Node not found")

        if action == "parent":
            # source becomes parent of target
            self._set_parent_child(nodes, source_id, target_id)
        elif action == "child":
            # source becomes child of target
            self._set_parent_child(nodes, target_id, source_id)
        elif action == "group":
            self._group_nodes(nodes, source_id, target_id)
        else:
            raise ValueError(f"Invalid action: {action}")

        self._save_nodes(nodes)

    def _set_parent_child(self, nodes: list, parent_id: str, child_id: str):
        """Set parent-child relationship, removing old parent if any."""
        parent = next(n for n in nodes if n["node_id"] == parent_id)
        child = next(n for n in nodes if n["node_id"] == child_id)
        # Remove child from old parent
        old_parent_id = child.get("parent_id")
        if old_parent_id:
            old_parent = next((n for n in nodes if n["node_id"] == old_parent_id), None)
            if old_parent and "children" in old_parent:
                old_parent["children"] = [c for c in old_parent["children"] if c != child_id]
        # Set new parent
        child["parent_id"] = parent_id
        if "children" not in parent:
            parent["children"] = []
        if child_id not in parent["children"]:
            parent["children"].append(child_id)

    def _group_nodes(self, nodes: list, id_a: str, id_b: str):
        """Group two nodes together. If one already has a group_id, add the other to it."""
        a = next(n for n in nodes if n["node_id"] == id_a)
        b = next(n for n in nodes if n["node_id"] == id_b)
        group_id_a = a.get("group_id")
        group_id_b = b.get("group_id")
        if group_id_a and group_id_b:
            # Merge: move all of b's group into a's group
            for n in nodes:
                if n.get("group_id") == group_id_b:
                    n["group_id"] = group_id_a
        elif group_id_a:
            b["group_id"] = group_id_a
        elif group_id_b:
            a["group_id"] = group_id_b
        else:
            # Create new group
            import uuid
            gid = "group-" + str(uuid.uuid4())[:8]
            a["group_id"] = gid
            b["group_id"] = gid

    def disconnect_nodes(self, source_id: str, target_id: str):
        """Remove parent-child relationship between two nodes."""
        nodes = self._load_nodes()
        source = next((n for n in nodes if n["node_id"] == source_id), None)
        target = next((n for n in nodes if n["node_id"] == target_id), None)
        if not source or not target:
            raise FileNotFoundError("Node not found")
        # Check if source is parent of target
        if target.get("parent_id") == source_id:
            target["parent_id"] = None
            if "children" in source:
                source["children"] = [c for c in source["children"] if c != target_id]
        # Check reverse
        elif source.get("parent_id") == target_id:
            source["parent_id"] = None
            if "children" in target:
                target["children"] = [c for c in target["children"] if c != source_id]
        self._save_nodes(nodes)

    def ungroup_node(self, node_id: str):
        """Remove a node from its group."""
        nodes = self._load_nodes()
        node = next((n for n in nodes if n["node_id"] == node_id), None)
        if not node:
            raise FileNotFoundError("Node not found")
        gid = node.get("group_id")
        if gid:
            node["group_id"] = None
            # If only one node left in group, remove group from that too
            remaining = [n for n in nodes if n.get("group_id") == gid]
            if len(remaining) == 1:
                remaining[0]["group_id"] = None
        self._save_nodes(nodes)

    def update_node(self, node_id: str, filename: str = None, content: str = None):
        """Update node name and/or knowledge content."""
        nodes = self._load_nodes()
        for n in nodes:
            if n["node_id"] == node_id:
                if filename is not None:
                    n["filename"] = filename
                if content is not None:
                    filepath = os.path.join(self.data_dir, f"{node_id}.txt")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    n["characters"] = len(content)
                break
        else:
            raise FileNotFoundError(f"Node not found: {node_id}")
        self._save_nodes(nodes)
