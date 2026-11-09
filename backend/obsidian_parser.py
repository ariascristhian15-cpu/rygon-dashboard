import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

class ObsidianMarkdownParser:
    """
    Parser bidireccional de Markdown compatible con Obsidian.
    Soporta Frontmatter YAML, Listas de Tareas (- [ ] / - [x]),
    Tablas Markdown y bloques estructurados.
    """

    @staticmethod
    def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """Extrae el frontmatter YAML y el cuerpo del markdown."""
        frontmatter = {}
        body = content
        pattern = r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        if match:
            fm_text = match.group(1)
            body = match.group(2)
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    # Tipos básicos
                    if val.lower() == "true":
                        val = True
                    elif val.lower() == "false":
                        val = False
                    elif val.isdigit():
                        val = int(val)
                    elif val.startswith("[") and val.endswith("]"):
                        # Lista simple [a, b, c]
                        val = [item.strip().strip("'\"") for item in val[1:-1].split(",") if item.strip()]
                    else:
                        val = val.strip("'\"")
                    frontmatter[key] = val
        return frontmatter, body

    @staticmethod
    def dump_frontmatter(frontmatter: Dict[str, Any], body: str) -> str:
        """Serializa frontmatter YAML y lo concatena al cuerpo."""
        if not frontmatter:
            return body
        lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                items = ", ".join(f'"{i}"' if " " in str(i) else str(i) for i in v)
                lines.append(f"{k}: [{items}]")
            elif isinstance(v, bool):
                lines.append(f"{k}: {'true' if v else 'false'}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")
        return "\n".join(lines) + body.lstrip("\r\n")

    @staticmethod
    def parse_task_list(body: str) -> List[Dict[str, Any]]:
        """
        Parsea listas de tareas tipo:
        - [ ] Tarea pendiente #tag
        - [x] Tarea completada
        """
        tasks = []
        task_regex = re.compile(r"^[-*]\s+\[([ xX])\]\s+(.*)$", re.MULTILINE)
        idx = 0
        for match in task_regex.finditer(body):
            status_char = match.group(1)
            raw_text = match.group(2).strip()
            completed = (status_char.lower() == "x")

            # Extraer tags como #sistemas, #urgente, etc.
            tags = re.findall(r"#([a-zA-Z0-9_\-]+)", raw_text)
            clean_text = re.sub(r"#[a-zA-Z0-9_\-]+", "", raw_text).strip()

            # Extraer metadata de porcentaje o prioridad si existe [P1], (80%)
            progress = 100 if completed else 0
            prog_match = re.search(r"\((\d+)%\)", raw_text)
            if prog_match:
                progress = int(prog_match.group(1))

            tasks.append({
                "id": f"task_{idx}",
                "text": clean_text,
                "raw": raw_text,
                "completed": completed,
                "tags": tags,
                "progress": progress
            })
            idx += 1
        return tasks

    @staticmethod
    def update_task_in_body(body: str, task_text_or_idx: Any, new_completed: bool) -> str:
        """Actualiza el estado de una tarea checkbox en el cuerpo Markdown."""
        lines = body.splitlines()
        task_regex = re.compile(r"^([-*]\s+\[)([ xX])(\]\s+)(.*)$")
        curr_idx = 0
        updated = False

        for i, line in enumerate(lines):
            m = task_regex.match(line)
            if m:
                text_part = m.group(4)
                match_condition = False
                if isinstance(task_text_or_idx, int) and curr_idx == task_text_or_idx:
                    match_condition = True
                elif isinstance(task_text_or_idx, str) and (task_text_or_idx in text_part or f"task_{curr_idx}" == task_text_or_idx):
                    match_condition = True

                if match_condition:
                    new_char = "x" if new_completed else " "
                    # Si tiene (100%) o (0%), actualizarlo
                    new_text_part = text_part
                    if new_completed and "(0%)" in new_text_part:
                        new_text_part = new_text_part.replace("(0%)", "(100%)")
                    elif not new_completed and "(100%)" in new_text_part:
                        new_text_part = new_text_part.replace("(100%)", "(0%)")
                    lines[i] = f"{m.group(1)}{new_char}{m.group(3)}{new_text_part}"
                    updated = True
                    break
                curr_idx += 1

        return "\n".join(lines)

    @staticmethod
    def parse_markdown_table(body: str) -> List[Dict[str, str]]:
        """Parsea tablas markdown a una lista de diccionarios."""
        rows = []
        lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
        if len(lines) < 2:
            return rows

        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        # Omitir la fila separadora |---|---|
        start_row = 1
        if len(lines) > 1 and re.match(r"^\|[\s\-:|]+\|$", lines[1]):
            start_row = 2

        for line in lines[start_row:]:
            cols = [c.strip() for c in line.strip("|").split("|")]
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = cols[i] if i < len(cols) else ""
            rows.append(row_dict)

        return rows

    @staticmethod
    def dump_markdown_table(headers: List[str], rows: List[Dict[str, Any]]) -> str:
        """Convierte una lista de registros en una tabla Markdown limpia."""
        if not headers or not rows:
            return ""

        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        data_lines = []

        for r in rows:
            line_vals = [str(r.get(h, "")).replace("|", "\\|") for h in headers]
            data_lines.append("| " + " | ".join(line_vals) + " |")

        return "\n".join([header_line, sep_line] + data_lines)
