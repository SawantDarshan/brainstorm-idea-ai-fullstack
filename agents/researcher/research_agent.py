"""Research Agent - searches the web, scrapes content, and creates a mind map of knowledge nodes."""

import json
import re
import uuid
import os
from engine.registry import get_engine
from pipelines.knowledge_pipeline import KnowledgePipeline

MIND_MAP_PROMPT = """You are a Research Mind Map AI. You have been given scraped web content about a topic. Your job is to analyze ALL the content and create a structured mind map.

Topic: {topic}

Rules:
- All information must be science-backed and factual
- Create ONE root node that summarizes the entire topic
- Create 3-7 branch nodes, each covering a distinct sub-topic
- Each branch node should have detailed, synthesized content (not just copy-paste)
- Include source URLs where relevant in the content
- Return ONLY valid JSON, no markdown, no explanation

Return format:
{{
  "root": {{
    "filename": "📚 Topic Title",
    "content": "Comprehensive overview summary of the topic..."
  }},
  "branches": [
    {{
      "filename": "🔬 Sub-topic Title",
      "content": "Detailed synthesized content about this sub-topic. Source: url..."
    }}
  ]
}}

Here is the scraped content:
{scraped_content}
"""


class ResearchAgent:
    """Agent that researches a topic online and creates a mind map cluster of nodes."""

    def __init__(self, knowledge_pipeline: KnowledgePipeline = None, on_step=None):
        self.pipeline = knowledge_pipeline or KnowledgePipeline()
        self.engine = get_engine()
        self.on_step = on_step  # callback: (step_id, status, text) -> None

    def _emit(self, step_id: str, status: str, text: str):
        if self.on_step:
            self.on_step(step_id, status, text)

    def _search_web(self, topic: str) -> list:
        """Search for science-backed information on the topic."""
        from apis.tavily_client import search
        query = f"{topic} research scientific evidence"
        results = search(query, num_results=5)
        return results

    def _scrape_urls(self, results: list) -> list:
        """Scrape content from search result URLs."""
        import requests
        from bs4 import BeautifulSoup
        from config.global_context import SCRAPE_TIMEOUT, SCRAPE_MAX_CHARS

        scraped = []
        for r in results[:5]:
            url = r.get("url", "")
            try:
                resp = requests.get(url, timeout=SCRAPE_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)[:SCRAPE_MAX_CHARS]
                scraped.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "content": text,
                })
            except Exception:
                scraped.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "content": r.get("snippet", ""),
                })
        return scraped

    def _build_mind_map(self, topic: str, scraped: list) -> dict:
        """Use LLM to structure scraped content into a mind map."""
        scraped_text = ""
        for s in scraped:
            scraped_text += f"\n--- Source: {s['title']} ({s['url']}) ---\n{s['content']}\n"

        llm = self.engine.create_llm()
        prompt = MIND_MAP_PROMPT.format(topic=topic, scraped_content=scraped_text[:8000])
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=prompt), HumanMessage(content=f"Create a mind map for: {topic}")]
        response = llm.invoke(messages)

        content = response.content.strip()
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            content = json_match.group(1).strip()
        try:
            plan = json.loads(content)
        except json.JSONDecodeError:
            brace_match = re.search(r'\{[\s\S]*\}', content)
            if brace_match:
                plan = json.loads(brace_match.group())
            else:
                raise ValueError(f"LLM did not return valid JSON: {content[:200]}")
        return plan

    def _create_node(self, filename: str, content: str, x: float, y: float, parent_id: str = None) -> str:
        """Create a knowledge node with content."""
        node_id = str(uuid.uuid4())
        filepath = os.path.join(self.pipeline.data_dir, f"{node_id}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        meta = {
            "node_id": node_id,
            "filename": filename,
            "characters": len(content),
            "x": x,
            "y": y,
            "parent_id": parent_id,
            "children": [],
            "node_type": "knowledge",
        }
        self.pipeline._add_node_meta(meta)
        return node_id

    def research(self, topic: str) -> dict:
        """Full research pipeline: search → scrape → mind map → create nodes."""
        results = {
            "topic": topic,
            "sources_found": 0,
            "sources_scraped": 0,
            "nodes_created": 0,
            "errors": [],
        }

        # Step 1: Search
        self._emit("search", "running", f"Searching the web for '{topic}'...")
        try:
            search_results = self._search_web(topic)
            results["sources_found"] = len(search_results)
            self._emit("search", "done", f"Found {len(search_results)} sources")
        except Exception as e:
            self._emit("search", "error", str(e))
            results["errors"].append(f"Search failed: {str(e)}")
            return results

        # Step 2: Scrape
        self._emit("scrape", "running", f"Scraping {len(search_results)} pages...")
        try:
            scraped = self._scrape_urls(search_results)
            results["sources_scraped"] = len([s for s in scraped if len(s.get("content", "")) > 50])
            self._emit("scrape", "done", f"Scraped {results['sources_scraped']} pages successfully")
        except Exception as e:
            self._emit("scrape", "error", str(e))
            results["errors"].append(f"Scrape failed: {str(e)}")
            return results

        # Step 3: Build mind map via LLM
        self._emit("generate", "running", "AI is analyzing content & generating mind map...")
        try:
            mind_map = self._build_mind_map(topic, scraped)
            branches_count = len(mind_map.get("branches", []))
            self._emit("generate", "done", f"Generated mind map with {branches_count} branches")
        except Exception as e:
            self._emit("generate", "error", str(e))
            results["errors"].append(f"Mind map generation failed: {str(e)}")
            return results

        # Step 4: Create nodes
        self._emit("create_nodes", "running", "Creating knowledge nodes on canvas...")
        try:
            # Find a good starting position (offset from existing nodes)
            all_nodes = self.pipeline.get_all_nodes()
            max_x = max((n.get("x", 0) for n in all_nodes), default=0)
            base_x = max(max_x + 100, 10100)
            base_y = 10100
            spacing_x = 300
            spacing_y = 140

            # Create root node
            root = mind_map.get("root", {})
            root_id = self._create_node(
                root.get("filename", f"📚 {topic}"),
                root.get("content", f"Research overview: {topic}"),
                base_x, base_y,
            )
            results["nodes_created"] += 1

            # Create branch nodes as children of root
            branches = mind_map.get("branches", [])
            for i, branch in enumerate(branches):
                bx = base_x + spacing_x
                by = base_y + i * spacing_y
                self._create_node(
                    branch.get("filename", f"🔬 Branch {i+1}"),
                    branch.get("content", ""),
                    bx, by,
                    parent_id=root_id,
                )
                results["nodes_created"] += 1

            # Group all research nodes together
            all_new_nodes = self.pipeline.get_all_nodes()
            research_ids = [n["node_id"] for n in all_new_nodes
                           if n.get("parent_id") == root_id or n["node_id"] == root_id]
            if len(research_ids) >= 2:
                self.pipeline.connect_nodes(research_ids[0], research_ids[1], "group")
                for rid in research_ids[2:]:
                    self.pipeline.connect_nodes(research_ids[0], rid, "group")

            self._emit("create_nodes", "done", f"Created {results['nodes_created']} nodes")
        except Exception as e:
            self._emit("create_nodes", "error", str(e))
            results["errors"].append(f"Node creation failed: {str(e)}")

        return results
