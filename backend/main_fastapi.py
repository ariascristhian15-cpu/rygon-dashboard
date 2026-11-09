"""
====================================================================
THIAN-CORE // FASTAPI IMPLEMENTATION (OPCIONAL)
====================================================================
Versión nativa con FastAPI, Pydantic y documentación Swagger (/docs).
Ejecutar con:
    uvicorn backend.main_fastapi:app --host 0.0.0.0 --port 8080 --reload
====================================================================
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .config import load_config, save_config
from .obsidian_sync import ObsidianSyncEngine

if FASTAPI_AVAILABLE:
    config = load_config()
    sync_engine = ObsidianSyncEngine(config["obsidian"]["vault_path"])

    app = FastAPI(
        title="THIAN-CORE API",
        description="API REST de sincronización con Bóveda de Obsidian",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    BASE_DIR = Path(__file__).resolve().parent.parent
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    # Modelos Pydantic
    class TaskTogglePayload(BaseModel):
        file_key: Optional[str] = None
        task_text: str
        completed: bool

    class StudyAddPayload(BaseModel):
        file_key: str
        section: str
        text: str
        tags: Optional[str] = ""

    class WorkshopAddPayload(BaseModel):
        category: str
        text: str
        tag: Optional[str] = "taller"

    class NotePayload(BaseModel):
        title: str
        content: str
        tags: Optional[List[str]] = []

    class ConfigPayload(BaseModel):
        vault_path: str

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = BASE_DIR / "templates" / "index.html"
        return FileResponse(index_file)

    @app.get("/api/stats")
    async def get_stats():
        return sync_engine.get_summary_stats()

    @app.get("/api/studies")
    async def get_studies():
        return sync_engine.get_studies_data()

    @app.post("/api/studies/toggle")
    async def toggle_study(data: TaskTogglePayload):
        ok = sync_engine.toggle_study_task(data.file_key, data.task_text, data.completed)
        return {"success": ok}

    @app.post("/api/studies/add")
    async def add_study(data: StudyAddPayload):
        ok = sync_engine.add_study_task(data.file_key, data.section, data.text, data.tags)
        return {"success": ok}

    @app.get("/api/rygon/inventory")
    async def get_inventory():
        return sync_engine.get_inventory()

    @app.post("/api/rygon/inventory")
    async def save_inventory(payload: Dict[str, Any]):
        item = payload.get("item")
        items = sync_engine.get_inventory()
        if item:
            idx = next((i for i, x in enumerate(items) if x.get("ID") == item.get("ID")), -1)
            if idx >= 0:
                items[idx] = item
            else:
                if not item.get("ID"):
                    item["ID"] = f"P-{len(items)+1:03d}"
                items.append(item)
            sync_engine.save_inventory(items)
        return {"success": True, "items": items}

    @app.delete("/api/rygon/inventory")
    async def delete_inventory(id: str = Query(...)):
        items = [i for i in sync_engine.get_inventory() if i.get("ID") != id]
        sync_engine.save_inventory(items)
        return {"success": True, "items": items}

    @app.get("/api/rygon/workshop")
    async def get_workshop():
        return sync_engine.get_workshop_tasks()

    @app.post("/api/rygon/workshop/toggle")
    async def toggle_workshop(data: TaskTogglePayload):
        ok = sync_engine.toggle_workshop_task(data.task_text, data.completed)
        return {"success": ok}

    @app.post("/api/rygon/workshop/add")
    async def add_workshop(data: WorkshopAddPayload):
        ok = sync_engine.add_workshop_task(data.category, data.text, data.tag)
        return {"success": ok}

    @app.get("/api/rygon/moodboard")
    async def get_moodboard():
        return sync_engine.get_moodboard()

    @app.post("/api/rygon/moodboard")
    async def save_moodboard(data: Dict[str, Any]):
        sync_engine.save_moodboard(data.get("raw_markdown", ""))
        return {"success": True}

    @app.get("/api/rygon/social")
    async def get_social():
        return sync_engine.get_social_planner()

    @app.post("/api/rygon/social")
    async def save_social(data: Dict[str, Any]):
        post = data.get("post")
        posts = sync_engine.get_social_planner()
        if post:
            idx = next((i for i, p in enumerate(posts) if p.get("ID") == post.get("ID")), -1)
            if idx >= 0:
                posts[idx] = post
            else:
                if not post.get("ID"):
                    post["ID"] = f"RED-{len(posts)+1:02d}"
                posts.append(post)
            sync_engine.save_social_planner(posts)
        return {"success": True, "posts": posts}

    @app.delete("/api/rygon/social")
    async def delete_social(id: str = Query(...)):
        posts = [p for p in sync_engine.get_social_planner() if p.get("ID") != id]
        sync_engine.save_social_planner(posts)
        return {"success": True, "posts": posts}

    @app.get("/api/habits")
    async def get_habits():
        return sync_engine.get_habits()

    @app.post("/api/habits/toggle")
    async def toggle_habit(data: TaskTogglePayload):
        ok = sync_engine.toggle_habit(data.task_text, data.completed)
        return {"success": ok}

    @app.get("/api/schedule")
    async def get_schedule():
        return sync_engine.get_schedule()

    @app.get("/api/quote")
    async def get_quote():
        return sync_engine.get_random_quote()

    @app.get("/api/notes")
    async def get_notes():
        return sync_engine.get_notes_list()

    @app.post("/api/notes")
    async def save_note(data: NotePayload):
        fn = sync_engine.create_or_update_note(data.title, data.content, data.tags)
        return {"success": True, "filename": fn}

    @app.delete("/api/notes")
    async def delete_note(filename: str = Query(...)):
        ok = sync_engine.delete_note(filename)
        return {"success": ok}

    @app.post("/api/sync/trigger")
    async def trigger_sync():
        stats = sync_engine.get_summary_stats()
        return {"status": "synced", "stats": stats}
else:
    # Si no está instalado FastAPI
    app = None
