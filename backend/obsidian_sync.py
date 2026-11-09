import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from .obsidian_parser import ObsidianMarkdownParser
from .sample_data import INITIAL_VAULT_FILES, MOTIVATIONAL_QUOTES

class ObsidianSyncEngine:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.parser = ObsidianMarkdownParser()
        self.file_mtimes = {}
        self.ensure_vault_structure()

    def ensure_vault_structure(self):
        """Crea la estructura de carpetas y archivos iniciales si no existen."""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Crear subdirectorios
        for folder in ["Estudios", "Rygon_Studio", "Rutinas", "Notas", ".obsidian"]:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

        # Configuración básica de Obsidian si no existe
        obsidian_config = self.vault_path / ".obsidian" / "app.json"
        if not obsidian_config.exists():
            with open(obsidian_config, "w", encoding="utf-8") as f:
                json.dump({
                    "legacyEditor": False,
                    "livePreview": True,
                    "showLineNumber": True,
                    "spellcheck": True
                }, f, indent=2)

        # Poblar archivos iniciales si están ausentes
        for rel_path, content in INITIAL_VAULT_FILES.items():
            file_path = self.vault_path / rel_path
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content.strip() + "\n")
            # Guardar mtime inicial
            if file_path.exists():
                self.file_mtimes[rel_path] = file_path.stat().st_mtime

    def _read_file(self, rel_path: str) -> str:
        """Lee el contenido de un archivo dentro de la bóveda."""
        file_path = self.vault_path / rel_path
        if not file_path.exists():
            return ""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, rel_path: str, content: str):
        """Escribe atómicamente un archivo dentro de la bóveda."""
        file_path = self.vault_path / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escritura atómica vía archivo temporal
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        temp_path.replace(file_path)
        
        self.file_mtimes[rel_path] = file_path.stat().st_mtime

    # ==========================================
    # 1. RESUMEN GLOBAL (STATS & DASHBOARD)
    # ==========================================
    def get_summary_stats(self) -> Dict[str, Any]:
        """Calcula estadísticas consolidadas de todos los módulos."""
        total_tasks = 0
        completed_tasks = 0

        # Tareas de Estudios
        for study_file in ["Estudios/Ingenieria_Sistemas.md", "Estudios/Diseno_Creativo.md", "Estudios/Electronica_Hardware.md"]:
            content = self._read_file(study_file)
            _, body = self.parser.parse_frontmatter(content)
            tasks = self.parser.parse_task_list(body)
            total_tasks += len(tasks)
            completed_tasks += sum(1 for t in tasks if t["completed"])

        # Tareas de Taller Rygon
        workshop_content = self._read_file("Rygon_Studio/Taller_Tareas.md")
        _, ws_body = self.parser.parse_frontmatter(workshop_content)
        ws_tasks = self.parser.parse_task_list(ws_body)
        total_tasks += len(ws_tasks)
        completed_tasks += sum(1 for t in ws_tasks if t["completed"])

        # Hábitos Diarios
        habits_content = self._read_file("Rutinas/Habitos_Diarios.md")
        fm_habits, h_body = self.parser.parse_frontmatter(habits_content)
        habits = self.parser.parse_task_list(h_body)
        total_habits = len(habits)
        completed_habits = sum(1 for h in habits if h["completed"])

        # Inventario Rygon
        inv_content = self._read_file("Rygon_Studio/Inventario.md")
        inv_rows = self.parser.parse_markdown_table(inv_content)
        total_products = len(inv_rows)
        low_stock_count = sum(1 for r in inv_rows if "Bajo" in r.get("Estado", "") or "Agotado" in r.get("Estado", ""))

        # Redes Sociales
        social_content = self._read_file("Rygon_Studio/Planificador_Redes.md")
        social_rows = self.parser.parse_markdown_table(social_content)
        published_posts = sum(1 for s in social_rows if "Publicado" in s.get("Estado", ""))

        pending_tasks = total_tasks - completed_tasks
        overall_progress = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        habits_progress = round((completed_habits / total_habits * 100), 1) if total_habits > 0 else 0

        return {
            "vault_path": str(self.vault_path),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "overall_progress": overall_progress,
            "habits_total": total_habits,
            "habits_completed": completed_habits,
            "habits_progress": habits_progress,
            "habits_streak": fm_habits.get("current_streak_days", 7),
            "inventory_products_count": total_products,
            "inventory_low_stock": low_stock_count,
            "social_posts_count": len(social_rows),
            "social_published": published_posts,
            "last_synced": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    # ==========================================
    # 2. MÓDULO DE ESTUDIOS Y CURSOS
    # ==========================================
    def get_studies_data(self) -> Dict[str, Any]:
        """Obtiene todas las rutas de aprendizaje con sus subsecciones y tareas."""
        result = {}
        files = {
            "sistemas": ("Estudios/Ingenieria_Sistemas.md", "💻 Ingeniería de Sistemas & Software"),
            "diseno": ("Estudios/Diseno_Creativo.md", "🎨 Diseño Digital & 3D"),
            "hardware": ("Estudios/Electronica_Hardware.md", "⚡ Electrónica & Hardware Básico")
        }

        for key, (rel_path, default_title) in files.items():
            content = self._read_file(rel_path)
            fm, body = self.parser.parse_frontmatter(content)
            
            # Parsear secciones con títulos nivel 2 (##)
            sections = []
            curr_section = None
            
            for line in body.splitlines():
                if line.startswith("## "):
                    if curr_section:
                        sections.append(curr_section)
                    curr_section = {
                        "title": line.replace("## ", "").strip(),
                        "tasks": []
                    }
                elif line.strip().startswith("- [") and curr_section:
                    task_parsed = self.parser.parse_task_list(line)
                    if task_parsed:
                        t = task_parsed[0]
                        # Asignar ID único con prefijo de archivo
                        t["file_key"] = key
                        curr_section["tasks"].append(t)

            if curr_section:
                sections.append(curr_section)

            # Re-asignar IDs unívocos en el archivo
            all_file_tasks = []
            task_counter = 0
            for sec in sections:
                for t in sec["tasks"]:
                    t["id"] = f"{key}_task_{task_counter}"
                    t["index"] = task_counter
                    task_counter += 1
                    all_file_tasks.append(t)

            total_t = len(all_file_tasks)
            comp_t = sum(1 for t in all_file_tasks if t["completed"])
            prog = round((comp_t / total_t * 100), 1) if total_t > 0 else 0

            result[key] = {
                "file_key": key,
                "rel_path": rel_path,
                "title": fm.get("title", default_title),
                "icon": fm.get("icon", "book"),
                "progress": prog,
                "total_tasks": total_t,
                "completed_tasks": comp_t,
                "sections": sections
            }

        return result

    def toggle_study_task(self, file_key: str, task_text: str, completed: bool) -> bool:
        """Actualiza el estado de una tarea de estudio directamente en el Markdown."""
        file_map = {
            "sistemas": "Estudios/Ingenieria_Sistemas.md",
            "diseno": "Estudios/Diseno_Creativo.md",
            "hardware": "Estudios/Electronica_Hardware.md"
        }
        rel_path = file_map.get(file_key)
        if not rel_path:
            return False

        content = self._read_file(rel_path)
        fm, body = self.parser.parse_frontmatter(content)
        
        new_body = self.parser.update_task_in_body(body, task_text, completed)
        
        # Recalcular progreso en frontmatter
        tasks = self.parser.parse_task_list(new_body)
        if tasks:
            fm["progress_overall"] = int(sum(1 for t in tasks if t["completed"]) / len(tasks) * 100)
            fm["updated"] = time.strftime("%Y-%m-%d")

        new_content = self.parser.dump_frontmatter(fm, new_body)
        self._write_file(rel_path, new_content)
        return True

    def add_study_task(self, file_key: str, section_title: str, task_text: str, tags: str = "") -> bool:
        """Agrega una nueva tarea a una sección específica en el archivo Markdown."""
        file_map = {
            "sistemas": "Estudios/Ingenieria_Sistemas.md",
            "diseno": "Estudios/Diseno_Creativo.md",
            "hardware": "Estudios/Electronica_Hardware.md"
        }
        rel_path = file_map.get(file_key)
        if not rel_path:
            return False

        content = self._read_file(rel_path)
        fm, body = self.parser.parse_frontmatter(content)

        formatted_tags = " " + tags.strip() if tags else ""
        new_task_line = f"- [ ] {task_text.strip()}{formatted_tags} (0%)"

        lines = body.splitlines()
        inserted = False
        target_found = False
        new_lines = []

        for i, line in enumerate(lines):
            new_lines.append(line)
            if section_title.lower() in line.lower() and line.startswith("## "):
                target_found = True
            elif target_found and (line.startswith("## ") or i == len(lines) - 1):
                # Insertar antes de la siguiente sección o al final
                if line.startswith("## "):
                    new_lines.insert(-1, new_task_line)
                else:
                    new_lines.append(new_task_line)
                inserted = True
                target_found = False

        if not inserted:
            new_lines.append(f"\n{new_task_line}")

        new_body = "\n".join(new_lines)
        new_content = self.parser.dump_frontmatter(fm, new_body)
        self._write_file(rel_path, new_content)
        return True

    # ==========================================
    # 3. MÓDULO RYGON STUDIO (TALLER & EMPRENDIMIENTO)
    # ==========================================
    def get_inventory(self) -> List[Dict[str, Any]]:
        """Devuelve los productos del inventario parseados de la tabla Markdown."""
        content = self._read_file("Rygon_Studio/Inventario.md")
        return self.parser.parse_markdown_table(content)

    def save_inventory(self, items: List[Dict[str, Any]]):
        """Guarda la lista completa de inventario en la tabla Markdown de Obsidian."""
        content = self._read_file("Rygon_Studio/Inventario.md")
        fm, body = self.parser.parse_frontmatter(content)

        headers = ["ID", "Producto", "Categoría", "Stock", "Precio_Venta", "Costo_Material", "Estado"]
        table_str = self.parser.dump_markdown_table(headers, items)

        # Reemplazar la tabla previa en el body
        table_pattern = r"\| ID \| Producto \|[\s\S]*?(?=\n\n|$)"
        if re.search(table_pattern, body):
            new_body = re.sub(table_pattern, table_str, body)
        else:
            # Buscar el encabezado de inventario
            header_idx = body.find("# 📦 Inventario")
            if header_idx != -1:
                new_body = body[:header_idx] + f"# 📦 Inventario Central - Rygon Studio\n\nControl de existencias, precios y materias primas.\n\n{table_str}\n"
            else:
                new_body = body + f"\n\n{table_str}\n"

        fm["updated"] = time.strftime("%Y-%m-%d")
        new_content = self.parser.dump_frontmatter(fm, new_body)
        self._write_file("Rygon_Studio/Inventario.md", new_content)

    def get_workshop_tasks(self) -> List[Dict[str, Any]]:
        """Devuelve las tareas de manufactura de taller (cerámica, crochet, etc.)."""
        content = self._read_file("Rygon_Studio/Taller_Tareas.md")
        fm, body = self.parser.parse_frontmatter(content)
        
        categories = []
        curr_cat = None
        for line in body.splitlines():
            if line.startswith("## "):
                if curr_cat:
                    categories.append(curr_cat)
                curr_cat = {
                    "category": line.replace("## ", "").strip(),
                    "tasks": []
                }
            elif line.strip().startswith("- [") and curr_cat:
                tasks_parsed = self.parser.parse_task_list(line)
                if tasks_parsed:
                    curr_cat["tasks"].append(tasks_parsed[0])

        if curr_cat:
            categories.append(curr_cat)

        idx = 0
        for cat in categories:
            for t in cat["tasks"]:
                t["id"] = f"workshop_{idx}"
                idx += 1

        return categories

    def toggle_workshop_task(self, task_text: str, completed: bool) -> bool:
        """Actualiza checkbox de tarea de taller en el archivo .md."""
        rel_path = "Rygon_Studio/Taller_Tareas.md"
        content = self._read_file(rel_path)
        fm, body = self.parser.parse_frontmatter(content)
        
        new_body = self.parser.update_task_in_body(body, task_text, completed)
        fm["updated"] = time.strftime("%Y-%m-%d")
        
        self._write_file(rel_path, self.parser.dump_frontmatter(fm, new_body))
        return True

    def add_workshop_task(self, category_title: str, task_text: str, tag: str = "") -> bool:
        """Agrega una nueva tarea a una categoría de taller."""
        rel_path = "Rygon_Studio/Taller_Tareas.md"
        content = self._read_file(rel_path)
        fm, body = self.parser.parse_frontmatter(content)

        tag_str = f" #{tag.strip()}" if tag else ""
        new_line = f"- [ ] {task_text.strip()}{tag_str} (0%)"

        lines = body.splitlines()
        new_lines = []
        target_found = False
        inserted = False

        for i, line in enumerate(lines):
            new_lines.append(line)
            if category_title.lower() in line.lower() and line.startswith("## "):
                target_found = True
            elif target_found and (line.startswith("## ") or i == len(lines) - 1):
                if line.startswith("## "):
                    new_lines.insert(-1, new_line)
                else:
                    new_lines.append(new_line)
                inserted = True
                target_found = False

        if not inserted:
            new_lines.append(f"\n## 🛠️ {category_title}\n{new_line}")

        new_body = "\n".join(new_lines)
        self._write_file(rel_path, self.parser.dump_frontmatter(fm, new_body))
        return True

    def get_moodboard(self) -> Dict[str, Any]:
        """Obtiene las notas y enlaces del moodboard."""
        content = self._read_file("Rygon_Studio/Inspiracion_Moodboard.md")
        fm, body = self.parser.parse_frontmatter(content)
        return {
            "title": fm.get("title", "Moodboard"),
            "raw_markdown": body,
            "tags": fm.get("tags", [])
        }

    def save_moodboard(self, markdown_body: str):
        """Guarda cambios en el archivo de moodboard."""
        rel_path = "Rygon_Studio/Inspiracion_Moodboard.md"
        content = self._read_file(rel_path)
        fm, _ = self.parser.parse_frontmatter(content)
        fm["updated"] = time.strftime("%Y-%m-%d")
        self._write_file(rel_path, self.parser.dump_frontmatter(fm, markdown_body))

    def get_social_planner(self) -> List[Dict[str, Any]]:
        """Obtiene la tabla de contenido programado para TikTok e Instagram."""
        content = self._read_file("Rygon_Studio/Planificador_Redes.md")
        return self.parser.parse_markdown_table(content)

    def save_social_planner(self, posts: List[Dict[str, Any]]):
        """Guarda la tabla del planificador de redes."""
        headers = ["ID", "Red_Social", "Titulo_Contenido", "Enfoque_Hook", "Fecha_Programada", "Estado"]
        table_str = self.parser.dump_markdown_table(headers, posts)

        content = self._read_file("Rygon_Studio/Planificador_Redes.md")
        fm, body = self.parser.parse_frontmatter(content)

        table_pattern = r"\| ID \| Red_Social \|[\s\S]*?(?=\n\n|$)"
        if re.search(table_pattern, body):
            new_body = re.sub(table_pattern, table_str, body)
        else:
            new_body = body + f"\n\n{table_str}\n"

        fm["updated"] = time.strftime("%Y-%m-%d")
        self._write_file("Rygon_Studio/Planificador_Redes.md", self.parser.dump_frontmatter(fm, new_body))

    # ==========================================
    # 4. MÓDULO DE HÁBITOS, HORARIOS Y FRASES
    # ==========================================
    def get_habits(self) -> Dict[str, Any]:
        """Obtiene la lista de hábitos diarios con estado y racha."""
        content = self._read_file("Rutinas/Habitos_Diarios.md")
        fm, body = self.parser.parse_frontmatter(content)
        tasks = self.parser.parse_task_list(body)
        return {
            "streak_days": fm.get("current_streak_days", 7),
            "best_streak": fm.get("best_streak_days", 21),
            "habits": tasks
        }

    def toggle_habit(self, habit_text: str, completed: bool) -> bool:
        """Marca o desmarca un hábito diario en el archivo .md."""
        rel_path = "Rutinas/Habitos_Diarios.md"
        content = self._read_file(rel_path)
        fm, body = self.parser.parse_frontmatter(content)
        new_body = self.parser.update_task_in_body(body, habit_text, completed)
        
        # Verificar si todos se completaron hoy para aumentar racha
        tasks = self.parser.parse_task_list(new_body)
        if tasks and all(t["completed"] for t in tasks):
            fm["current_streak_days"] = fm.get("current_streak_days", 0) + 1
            if fm["current_streak_days"] > fm.get("best_streak_days", 0):
                fm["best_streak_days"] = fm["current_streak_days"]

        fm["updated"] = time.strftime("%Y-%m-%d")
        self._write_file(rel_path, self.parser.dump_frontmatter(fm, new_body))
        return True

    def get_schedule(self) -> List[Dict[str, str]]:
        """Obtiene el horario semanal estructurado."""
        content = self._read_file("Rutinas/Horario_Semanal.md")
        return self.parser.parse_markdown_table(content)

    def get_random_quote(self) -> Dict[str, str]:
        """Retorna una frase motivacional aleatoria estilo terminal/pixel-art."""
        import random
        return random.choice(MOTIVATIONAL_QUOTES)

    # ==========================================
    # 5. NOTAS RÁPIDAS (OBSIDIAN VAULT)
    # ==========================================
    def get_notes_list(self) -> List[Dict[str, Any]]:
        """Lista todas las notas de la carpeta Notas/."""
        notes_dir = self.vault_path / "Notas"
        notes = []
        if notes_dir.exists():
            for p in sorted(notes_dir.glob("*.md"), key=os.path.getmtime, reverse=True):
                content = p.read_text(encoding="utf-8")
                fm, body = self.parser.parse_frontmatter(content)
                notes.append({
                    "filename": p.name,
                    "title": fm.get("title", p.stem),
                    "created": fm.get("created", time.strftime("%Y-%m-%d")),
                    "tags": fm.get("tags", []),
                    "preview": body[:140].strip() + ("..." if len(body) > 140 else ""),
                    "content": body
                })
        return notes

    def create_or_update_note(self, title: str, content: str, tags: List[str] = None) -> str:
        """Crea o actualiza una nota .md en la carpeta Notas/ de Obsidian."""
        safe_name = re.sub(r"[^\w\-_]", "_", title.strip()) + ".md"
        rel_path = f"Notas/{safe_name}"
        
        fm = {
            "title": title.strip(),
            "category": "Notas",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": tags or ["nota-rapida"]
        }
        full_content = self.parser.dump_frontmatter(fm, content.strip() + "\n")
        self._write_file(rel_path, full_content)
        return safe_name

    def delete_note(self, filename: str) -> bool:
        """Elimina una nota de la carpeta Notas/."""
        target = self.vault_path / "Notas" / filename
        if target.exists() and target.is_file():
            target.unlink()
            return True
        return False
