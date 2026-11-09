#!/usr/bin/env python3
"""
====================================================================
THIAN-CORE // RETRO WORKSTATION & OBSIDIAN PRODUCTIVITY HUB
====================================================================
Servidor Web Full-Stack local con sincronización bidireccional
a Bóveda de Obsidian en Linux Fedora.
Ejecutable sin dependencias externas obligatorias (Pure Python 3 stdlib)
y compatible con FastAPI / Flask.
====================================================================
"""

import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ajustar path para importar backend
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import load_config, save_config
from backend.obsidian_sync import ObsidianSyncEngine

# Cargar configuración inicial y sincronizador
CONFIG = load_config()
SYNC_ENGINE = ObsidianSyncEngine(CONFIG["obsidian"]["vault_path"])

class RetroHubRequestHandler(BaseHTTPRequestHandler):
    """Router y manejador de peticiones HTTP REST + Archivos Estáticos."""

    def log_message(self, format, *args):
        # Log formateado estilo terminal retro
        print(f"[\033[33mTHIAN-NET\033[0m] {self.command} {self.path} - {args[0]}")

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Rutas de Frontend y Estáticos
        if path == "/" or path == "/index.html":
            self._serve_template("index.html")
            return
        elif path.startswith("/static/"):
            self._serve_static(path[8:])
            return

        # 2. Rutas de API REST
        try:
            if path == "/api/stats":
                self._send_json(SYNC_ENGINE.get_summary_stats())
            elif path == "/api/studies":
                self._send_json(SYNC_ENGINE.get_studies_data())
            elif path == "/api/rygon/inventory":
                self._send_json(SYNC_ENGINE.get_inventory())
            elif path == "/api/rygon/workshop":
                self._send_json(SYNC_ENGINE.get_workshop_tasks())
            elif path == "/api/rygon/moodboard":
                self._send_json(SYNC_ENGINE.get_moodboard())
            elif path == "/api/rygon/social":
                self._send_json(SYNC_ENGINE.get_social_planner())
            elif path == "/api/habits":
                self._send_json(SYNC_ENGINE.get_habits())
            elif path == "/api/schedule":
                self._send_json(SYNC_ENGINE.get_schedule())
            elif path == "/api/quote":
                self._send_json(SYNC_ENGINE.get_random_quote())
            elif path == "/api/notes":
                self._send_json(SYNC_ENGINE.get_notes_list())
            elif path == "/api/config":
                self._send_json(CONFIG)
            elif path == "/api/health":
                self._send_json({"status": "OK", "os": "Fedora Linux", "engine": "ObsidianSync"})
            else:
                self.send_error(404, f"Endpoint no encontrado: {path}")
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def do_POST(self):
        global SYNC_ENGINE
        parsed = urlparse(self.path)
        path = parsed.path
        payload = self._read_json_body()

        try:
            # Sincronización Manual o Recarga
            if path == "/api/sync/trigger":
                stats = SYNC_ENGINE.get_summary_stats()
                self._send_json({"status": "synced", "stats": stats})

            # Tareas de Estudios
            elif path == "/api/studies/toggle":
                file_key = payload.get("file_key")
                task_text = payload.get("task_text")
                completed = payload.get("completed", False)
                success = SYNC_ENGINE.toggle_study_task(file_key, task_text, completed)
                self._send_json({"success": success})

            elif path == "/api/studies/add":
                file_key = payload.get("file_key")
                section = payload.get("section")
                text = payload.get("text")
                tags = payload.get("tags", "")
                success = SYNC_ENGINE.add_study_task(file_key, section, text, tags)
                self._send_json({"success": success})

            # Inventario Rygon Studio
            elif path == "/api/rygon/inventory":
                items = SYNC_ENGINE.get_inventory()
                item_data = payload.get("item")
                if item_data:
                    # Si ya existe por ID, actualizarlo, de lo contrario agregar
                    existing_idx = next((i for i, it in enumerate(items) if it.get("ID") == item_data.get("ID")), -1)
                    if existing_idx >= 0:
                        items[existing_idx] = item_data
                    else:
                        if not item_data.get("ID"):
                            item_data["ID"] = f"P-{len(items)+1:03d}"
                        items.append(item_data)
                    SYNC_ENGINE.save_inventory(items)
                self._send_json({"success": True, "items": items})

            # Taller Rygon
            elif path == "/api/rygon/workshop/toggle":
                task_text = payload.get("task_text")
                completed = payload.get("completed", False)
                success = SYNC_ENGINE.toggle_workshop_task(task_text, completed)
                self._send_json({"success": success})

            elif path == "/api/rygon/workshop/add":
                category = payload.get("category", "Taller")
                text = payload.get("text")
                tag = payload.get("tag", "taller")
                success = SYNC_ENGINE.add_workshop_task(category, text, tag)
                self._send_json({"success": success})

            # Moodboard
            elif path == "/api/rygon/moodboard":
                markdown_body = payload.get("raw_markdown", "")
                SYNC_ENGINE.save_moodboard(markdown_body)
                self._send_json({"success": True})

            # Redes Sociales
            elif path == "/api/rygon/social":
                posts = SYNC_ENGINE.get_social_planner()
                post_data = payload.get("post")
                if post_data:
                    existing_idx = next((i for i, p in enumerate(posts) if p.get("ID") == post_data.get("ID")), -1)
                    if existing_idx >= 0:
                        posts[existing_idx] = post_data
                    else:
                        if not post_data.get("ID"):
                            post_data["ID"] = f"RED-{len(posts)+1:02d}"
                        posts.append(post_data)
                    SYNC_ENGINE.save_social_planner(posts)
                self._send_json({"success": True, "posts": posts})

            # Hábitos Diarios
            elif path == "/api/habits/toggle":
                habit_text = payload.get("habit_text")
                completed = payload.get("completed", False)
                success = SYNC_ENGINE.toggle_habit(habit_text, completed)
                self._send_json({"success": success})

            # Notas de Obsidian
            elif path == "/api/notes":
                title = payload.get("title", "Nota")
                content = payload.get("content", "")
                tags = payload.get("tags", [])
                filename = SYNC_ENGINE.create_or_update_note(title, content, tags)
                self._send_json({"success": True, "filename": filename})

            # Configuración
            elif path == "/api/config":
                new_vault = payload.get("vault_path")
                if new_vault:
                    CONFIG["obsidian"]["vault_path"] = os.path.abspath(os.path.expanduser(new_vault))
                    save_config(CONFIG)
                    SYNC_ENGINE = ObsidianSyncEngine(CONFIG["obsidian"]["vault_path"])
                self._send_json({"success": True, "config": CONFIG})

            else:
                self.send_error(404, f"Endpoint POST no encontrado: {path}")
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        try:
            if path == "/api/rygon/inventory":
                item_id = qs.get("id", [None])[0]
                if item_id:
                    items = SYNC_ENGINE.get_inventory()
                    items = [it for it in items if it.get("ID") != item_id]
                    SYNC_ENGINE.save_inventory(items)
                    self._send_json({"success": True, "items": items})
                else:
                    self._send_json({"error": "ID requerido"}, status=400)

            elif path == "/api/rygon/social":
                post_id = qs.get("id", [None])[0]
                if post_id:
                    posts = SYNC_ENGINE.get_social_planner()
                    posts = [p for p in posts if p.get("ID") != post_id]
                    SYNC_ENGINE.save_social_planner(posts)
                    self._send_json({"success": True, "posts": posts})
                else:
                    self._send_json({"error": "ID requerido"}, status=400)

            elif path == "/api/notes":
                filename = qs.get("filename", [None])[0]
                if filename:
                    success = SYNC_ENGINE.delete_note(filename)
                    self._send_json({"success": success})
                else:
                    self._send_json({"error": "filename requerido"}, status=400)
            else:
                self.send_error(404, f"Endpoint DELETE no encontrado: {path}")
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _serve_template(self, template_name: str):
        file_path = BASE_DIR / "templates" / template_name
        if not file_path.exists():
            self.send_error(404, "Plantilla HTML no encontrada")
            return
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_static(self, rel_path: str):
        file_path = BASE_DIR / "static" / rel_path
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, f"Archivo estático no encontrado: {rel_path}")
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

def run_server():
    host = CONFIG["server"]["host"]
    port = CONFIG["server"]["port"]
    
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, RetroHubRequestHandler)
    
    print("\n" + "=" * 62)
    print(" 🕹️  THIAN-CORE // ESTACIÓN CENTRAL DE PRODUCTIVIDAD Y OBSIDIAN")
    print("=" * 62)
    print(f" ▶ Servidor Web activo en : http://localhost:{port}")
    print(f" ▶ Bóveda de Obsidian     : {CONFIG['obsidian']['vault_path']}")
    print(f" ▶ Plataforma             : Fedora Linux (Python 3.15)")
    print(f" ▶ Sincronización         : Bidireccional Automática Activada")
    print("=" * 62 + "\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[THIAN-CORE] Servidor detenido con éxito.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
