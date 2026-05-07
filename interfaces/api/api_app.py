import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from interfaces.adapters.base_adapter import AdapterRequest
from interfaces.adapters.research_adapter import ResearchAdapter
from pipelines.knowledge_pipeline import KnowledgePipeline
from auth.auth import get_current_user

app = FastAPI(
    title="Multi-Agent Research System",
    version="2.0.0",
    description="Production-ready API for AI-powered research agents",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML/CSS)
_static_dir = os.path.join(os.path.dirname(__file__), "..", "web", "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Pipeline singletons
_knowledge_pipeline = KnowledgePipeline()
_research_adapter = ResearchAdapter()


class ResearchRequest(BaseModel):
    topic: str


class ResearchResponse(BaseModel):
    success: bool
    topic: str
    report: str
    critique: str
    metadata: dict
    error: Optional[str] = None


# --- Public routes ---

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(os.path.join(_static_dir, "index.html"))

@app.get("/login", include_in_schema=False)
async def login_page():
    return FileResponse(os.path.join(_static_dir, "login.html"))

@app.get("/dashboard", include_in_schema=False)
async def dashboard_page():
    return FileResponse(os.path.join(_static_dir, "dashboard.html"))

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), x: float = 0, y: float = 0, current_user: dict = Depends(get_current_user)):
    """Upload a file, extract text via KnowledgePipeline, and save as knowledge."""
    try:
        contents = await file.read()
        result = _knowledge_pipeline.process(contents, file.filename, x=x, y=y)
        return {"status": "ok", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.post("/api/notes/generate")
async def generate_notes(file: UploadFile = File(None), text: str = "", title: str = "", current_user: dict = Depends(get_current_user)):
    """Generate mind-map notes from text or uploaded file. Uses LLM to split into root + branches."""
    import uuid as _uuid
    try:
        content = ""
        source_name = title or "Notes"
        # Get content from file or text
        if file and file.filename:
            contents = await file.read()
            ext = os.path.splitext(file.filename)[1].lower()
            if ext == ".pdf":
                content = _knowledge_pipeline.extract_text(contents, file.filename)
                source_name = title or file.filename
            elif ext in (".txt", ".md"):
                content = contents.decode("utf-8", errors="ignore")
                source_name = title or file.filename
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        elif text.strip():
            content = text.strip()
            source_name = title or content[:40]
        else:
            raise HTTPException(status_code=400, detail="Provide text or a file.")

        if not content.strip():
            raise HTTPException(status_code=400, detail="No content could be extracted.")

        # Use LLM to break into mind map
        from config.global_context import ENGINE_PROVIDER
        if ENGINE_PROVIDER == "openai":
            from engine.openai_engine import OpenAIEngine
            engine = OpenAIEngine()
        else:
            from engine.ollama_engine import OllamaEngine
            engine = OllamaEngine()

        llm = engine.create_llm()
        from langchain_core.messages import SystemMessage, HumanMessage
        import json as _json

        mind_map_prompt = f"""Analyze the following content and create a mind map structure.
Break it into a root topic and 3-8 branch topics (key concepts, sections, or ideas).

Return ONLY valid JSON (no markdown fences):
{{
  "root": {{"title": "Main Topic Title", "summary": "Brief overview (2-3 sentences)"}},
  "branches": [
    {{"title": "Branch Title", "content": "Detailed notes for this branch (3-5 sentences)", "emoji": "relevant emoji"}},
    ...
  ]
}}

Content to analyze:
{content[:6000]}"""

        response = llm.invoke([SystemMessage(content=mind_map_prompt), HumanMessage(content="Generate the mind map.")])
        resp_text = response.content.strip()

        # Parse JSON
        import re
        try:
            mind_map = _json.loads(resp_text)
        except _json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', resp_text)
            if match:
                mind_map = _json.loads(match.group())
            else:
                raise ValueError("LLM did not return valid JSON")

        # Create nodes
        all_nodes = _knowledge_pipeline.get_all_nodes()
        max_x = max((n.get("x", 0) for n in all_nodes), default=10000)
        base_x = max(max_x + 200, 10200)
        base_y = 10100

        created_nodes = []

        # Root node
        root = mind_map.get("root", {})
        root_id = str(_uuid.uuid4())
        root_text = f"{root.get('title', source_name)}\n\n{root.get('summary', content[:200])}"
        root_path = os.path.join(_knowledge_pipeline.data_dir, f"{root_id}.txt")
        with open(root_path, "w", encoding="utf-8") as f:
            f.write(root_text)
        root_meta = {
            "node_id": root_id,
            "filename": f"📚 {root.get('title', source_name)}",
            "characters": len(root_text),
            "x": base_x, "y": base_y,
            "parent_id": None, "node_type": "knowledge",
        }
        _knowledge_pipeline._add_node_meta(root_meta)
        created_nodes.append(root_meta)

        # Branch nodes
        branches = mind_map.get("branches", [])
        spacing_y = 120
        for i, branch in enumerate(branches):
            bid = str(_uuid.uuid4())
            emoji = branch.get("emoji", "📝")
            btitle = branch.get("title", f"Branch {i+1}")
            bcontent = branch.get("content", "")
            btext = f"{btitle}\n\n{bcontent}"
            bpath = os.path.join(_knowledge_pipeline.data_dir, f"{bid}.txt")
            with open(bpath, "w", encoding="utf-8") as f:
                f.write(btext)
            bmeta = {
                "node_id": bid,
                "filename": f"{emoji} {btitle}",
                "characters": len(btext),
                "x": base_x + 300, "y": base_y + i * spacing_y,
                "parent_id": root_id, "node_type": "knowledge",
            }
            _knowledge_pipeline._add_node_meta(bmeta)
            created_nodes.append(bmeta)

        # Group them
        if len(created_nodes) >= 2:
            try:
                _knowledge_pipeline.connect_nodes(created_nodes[0]["node_id"], created_nodes[1]["node_id"], "group")
                for n in created_nodes[2:]:
                    _knowledge_pipeline.connect_nodes(created_nodes[0]["node_id"], n["node_id"], "group")
            except Exception:
                pass

        return {"status": "ok", "nodes_created": len(created_nodes), "nodes": created_nodes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nodes")
async def get_nodes(current_user: dict = Depends(get_current_user)):
    """Return all saved nodes."""
    return _knowledge_pipeline.get_all_nodes()

class UpdateNodeRequest(BaseModel):
    filename: Optional[str] = None
    content: Optional[str] = None

@app.put("/api/nodes/{node_id}")
async def update_node(node_id: str, request: UpdateNodeRequest, current_user: dict = Depends(get_current_user)):
    """Update node name and/or content."""
    try:
        _knowledge_pipeline.update_node(node_id, filename=request.filename, content=request.content)
        return {"status": "ok", "node_id": node_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UpdatePositionRequest(BaseModel):
    x: float
    y: float

@app.patch("/api/nodes/{node_id}/position")
async def update_node_position(node_id: str, request: UpdatePositionRequest, current_user: dict = Depends(get_current_user)):
    """Update node position after drag."""
    try:
        _knowledge_pipeline.update_node_position(node_id, request.x, request.y)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/nodes/{node_id}")
async def delete_node(node_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a node and its knowledge file."""
    try:
        _knowledge_pipeline.delete_node(node_id)
        return {"status": "ok", "node_id": node_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConnectRequest(BaseModel):
    source_id: str
    target_id: str
    action: str  # "parent", "child", or "group"

class DisconnectRequest(BaseModel):
    source_id: str
    target_id: str

class UngroupRequest(BaseModel):
    node_id: str

@app.post("/api/nodes/connect")
async def connect_nodes(request: ConnectRequest, current_user: dict = Depends(get_current_user)):
    """Connect two nodes as parent/child or group them."""
    try:
        _knowledge_pipeline.connect_nodes(request.source_id, request.target_id, request.action)
        return {"status": "ok"}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/nodes/disconnect")
async def disconnect_nodes(request: DisconnectRequest, current_user: dict = Depends(get_current_user)):
    """Remove parent-child relationship."""
    try:
        _knowledge_pipeline.disconnect_nodes(request.source_id, request.target_id)
        return {"status": "ok"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/nodes/ungroup")
async def ungroup_node(request: UngroupRequest, current_user: dict = Depends(get_current_user)):
    """Remove a node from its group."""
    try:
        _knowledge_pipeline.ungroup_node(request.node_id)
        return {"status": "ok"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

class AgentAskRequest(BaseModel):
    node_ids: list
    question: str

@app.post("/api/agent/ask")
async def agent_ask(request: AgentAskRequest, current_user: dict = Depends(get_current_user)):
    """Ask the support agent a question using selected node knowledge."""
    if not request.node_ids:
        raise HTTPException(status_code=400, detail="No nodes selected.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")
    try:
        from agents.support.support_agent import SupportAgent
        agent = SupportAgent(_knowledge_pipeline)

        async def generate():
            for chunk in agent.ask_stream(request.node_ids, request.question):
                yield chunk

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ResearchRequest2(BaseModel):
    topic: str

@app.post("/api/agent/research")
async def agent_research(request: ResearchRequest2, current_user: dict = Depends(get_current_user)):
    """Research a topic online and create a mind map of knowledge nodes."""
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is empty.")
    try:
        from agents.researcher.research_agent import ResearchAgent
        agent = ResearchAgent(_knowledge_pipeline)
        result = agent.research(request.topic.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class OrganizeRequest(BaseModel):
    pattern: str = "categories"
    custom_instruction: str = ""

@app.post("/api/agent/organize")
async def agent_organize(request: OrganizeRequest, current_user: dict = Depends(get_current_user)):
    """Use AI to auto-organize all canvas nodes into groups, hierarchies, and remove duplicates."""
    try:
        from agents.organizer.organizer_agent import OrganizerAgent
        agent = OrganizerAgent(_knowledge_pipeline)
        result = agent.organize(pattern=request.pattern, custom_instruction=request.custom_instruction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ConverseRequest(BaseModel):
    message: str
    conversation_history: list = []
    selected_node_ids: list = []

@app.post("/api/agent/converse")
async def agent_converse(request: ConverseRequest, current_user: dict = Depends(get_current_user)):
    """Conversational AI agent that detects intent and dispatches actions."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty.")
    try:
        from agents.planner.planner_agent import PlannerAgent
        agent = PlannerAgent(_knowledge_pipeline)

        async def generate():
            for line in agent.converse(
                message=request.message.strip(),
                conversation_history=request.conversation_history,
                selected_node_ids=request.selected_node_ids,
            ):
                yield line

        return StreamingResponse(generate(), media_type="application/x-ndjson")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    session_id: str
    message: str
    source: str = "text"  # "text" or "voice"

@app.post("/api/chat")
async def chat_message(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Save a chat/voice message as a new knowledge node."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        import uuid
        from pipelines.knowledge_pipeline import KnowledgePipeline
        parent_id = KnowledgePipeline.SYSTEM_VOICE_ID if request.source == "voice" else KnowledgePipeline.SYSTEM_CHAT_ID
        # Get parent to calculate child position
        nodes = _knowledge_pipeline.get_all_nodes()
        parent = next((n for n in nodes if n["node_id"] == parent_id), None)
        siblings = [n for n in nodes if n.get("parent_id") == parent_id]
        px = parent["x"] if parent else 10040
        py = parent["y"] if parent else 10500
        child_y = py + 100 + len(siblings) * 70

        node_id = str(uuid.uuid4())
        filepath = os.path.join(_knowledge_pipeline.data_dir, f"{node_id}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(request.message)
        meta = {
            "node_id": node_id,
            "filename": f"{'🎤' if request.source == 'voice' else '💬'} {request.message[:30]}",
            "characters": len(request.message),
            "x": px,
            "y": child_y,
            "parent_id": parent_id,
            "node_type": "conversation",
            "session_id": request.session_id,
            "source": request.source,
        }
        _knowledge_pipeline._add_node_meta(meta)
        return {"status": "ok", **meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/{node_id}")
async def stream_knowledge(node_id: str, current_user: dict = Depends(get_current_user)):
    """Stream back the extracted knowledge text for a node."""
    try:
        text = _knowledge_pipeline.load_knowledge(node_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Knowledge not found for node: {node_id}")

    async def generate():
        chunk_size = 200
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]

    return StreamingResponse(generate(), media_type="text/plain")

@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest, current_user: dict = Depends(get_current_user)):
    adapter_req = AdapterRequest(topic=request.topic)
    result = _research_adapter.execute(adapter_req)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return ResearchResponse(
        success=result.success,
        topic=result.topic,
        report=result.report,
        critique=result.critique,
        metadata=result.metadata,
    )


# =============================================================================
# PROVIDER SETTINGS ENDPOINTS
# =============================================================================

class ProviderSettingsRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None


@app.get("/api/providers")
async def get_providers(current_user: dict = Depends(get_current_user)):
    """Get all available providers and current settings."""
    from engine.registry import PROVIDERS, load_settings
    settings = load_settings()
    providers_list = []
    for key, info in PROVIDERS.items():
        providers_list.append({
            "id": key,
            "name": info["name"],
            "description": info["description"],
            "requires_api_key": info["requires_api_key"],
            "models": info["models"],
            "is_active": key == settings.get("active_provider"),
            "has_api_key": bool(settings.get("api_keys", {}).get(key)),
        })
    return {
        "providers": providers_list,
        "active_provider": settings.get("active_provider", "ollama"),
        "active_model": settings.get("active_model", "qwen3.5"),
    }


@app.post("/api/providers/active")
async def set_active_provider(req: ProviderSettingsRequest, current_user: dict = Depends(get_current_user)):
    """Set active provider, model, and optionally save API key."""
    from engine.registry import PROVIDERS, load_settings, save_settings
    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")

    settings = load_settings()
    settings["active_provider"] = req.provider
    if req.model:
        settings["active_model"] = req.model
    elif req.provider != settings.get("active_provider"):
        # Default to first model of new provider
        settings["active_model"] = PROVIDERS[req.provider]["models"][0]

    if req.api_key:
        if "api_keys" not in settings:
            settings["api_keys"] = {}
        settings["api_keys"][req.provider] = req.api_key

    save_settings(settings)
    return {"success": True, "active_provider": req.provider, "active_model": settings["active_model"]}


@app.post("/api/providers/test")
async def test_provider(req: ProviderSettingsRequest, current_user: dict = Depends(get_current_user)):
    """Test connection to a provider."""
    from engine.registry import get_engine
    try:
        engine = get_engine(provider=req.provider, model=req.model, api_key=req.api_key)
        llm = engine.create_llm()
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'hello' in one word.")])
        return {"success": True, "response": response.content[:100]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def start():
    import uvicorn
    from config.global_context import API_HOST, API_PORT
    uvicorn.run(app, host=API_HOST, port=int(API_PORT))
