"""
====================================================================
THIAN-CORE // WEEKLY HISTORY & XP RESET ENGINE
====================================================================
Motor de ciclos semanales para la bóveda de Obsidian.

Responsabilidades:
  1. Calcular el rendimiento de la semana actual a partir de las tareas
     reales de Estudios, Rygon Studio y Hábitos.
  2. Guardar un registro definitivo en data/weekly_history.json.
  3. Reiniciar el contador semanal usando una línea base (baseline) de
     tareas ya completadas, SIN borrar ni desmarcar la estructura de los
     archivos Markdown.
  4. Replicar los registros en Supabase (tabla weekly_history) cuando
     las credenciales están configuradas.

El módulo usa solo la librería estándar de Python 3.
====================================================================
"""

import json
import os
import re
import threading
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib import request

from .config import BASE_DIR

DEFAULT_USER_ID = "thian-core"
DEFAULT_XP_PER_TASK = 25
DEFAULT_XP_PER_HABIT = 50
DEFAULT_XP_PER_LEVEL = 500

MODULE_LABELS = {
    "estudios": "Estudios",
    "rygon": "Rygon Studio",
    "rutinas": "Hábitos",
}


# ====================================================================
# HELPERS DE FECHAS Y CLAVES DE TAREAS
# ====================================================================
def monday_of(day: date) -> date:
    """Devuelve el lunes de la semana ISO a la que pertenece `day`."""
    return day - timedelta(days=day.weekday())


def safe_date(value: Any, fallback: date) -> date:
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return fallback


def clean_task_key(module: str, scope: str, raw: Any) -> str:
    """
    Genera una clave estable para una tarea.

    Importante: se elimina el porcentaje (0%) / (100%) del texto para que
    la clave NO cambie cuando el usuario marca o desmarca el checkbox.
    """
    text = re.sub(r"\(\s*\d+\s*%\s*\)", "", str(raw or ""))
    text = re.sub(r"\s+", " ", text).strip().lower()
    scope_clean = re.sub(r"\s+", " ", str(scope or "")).strip().lower()
    return f"{module}:{scope_clean}:{text}"


# ====================================================================
# ESPEJO OPCIONAL A SUPABASE (REST API, SIN DEPENDENCIAS)
# ====================================================================
class SupabaseMirror:
    """Replica registros en Supabase usando PostgREST + urllib."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.url = (
            os.environ.get("SUPABASE_URL")
            or cfg.get("url")
            or ""
        ).strip()
        self.key = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("SUPABASE_KEY")
            or cfg.get("publishable_key")
            or cfg.get("anon_key")
            or ""
        ).strip()
        self.table = str(cfg.get("table") or "weekly_history")
        self.timeout = float(cfg.get("timeout_seconds") or 4)
        self._last_error_at = 0.0
        self._last_error = ""

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.url and self.key)

    def _endpoint(self) -> str:
        base = self.url.rstrip("/")
        if base.endswith("/rest/v1"):
            return f"{base}/{self.table}"
        return f"{base}/rest/v1/{self.table}"

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def _note_error(self, exc: Exception):
        self._last_error = str(exc)
        now = time.time()
        if now - self._last_error_at > 60:
            print(f"[WEEKLY][SUPABASE] Sincronización omitida: {exc}")
            self._last_error_at = now

    def upsert(self, record: Dict[str, Any]) -> bool:
        if not self.configured:
            return False

        payload = {
            "id": record.get("id"),
            "user_id": record.get("user_id"),
            "week_start_date": record.get("week_start_date"),
            "week_end_date": record.get("week_end_date"),
            "total_tasks": int(record.get("total_tasks") or 0),
            "completed_tasks": int(record.get("completed_tasks") or 0),
            "xp_earned": int(record.get("xp_earned") or 0),
            "effectiveness_percentage": float(
                record.get("effectiveness_percentage") or 0
            ),
            "status": record.get("status") or "completed",
            "breakdown": record.get("breakdown") or {},
            "source": record.get("source") or "manual",
            "closed_at": record.get("closed_at"),
        }

        url = f"{self._endpoint()}?on_conflict=user_id,week_start_date"
        req = request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                **self._headers(),
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                return 200 <= getattr(resp, "status", 0) < 300
        except Exception as exc:  # noqa: BLE001 - red/offline es no fatal
            self._note_error(exc)
            return False

    def fetch_all(self) -> List[Dict[str, Any]]:
        if not self.configured:
            return []
        if self._last_error_at and (time.time() - self._last_error_at) < 60:
            return []

        url = (
            f"{self._endpoint()}?select=*"
            "&order=week_start_date.desc&limit=200"
        )
        req = request.Request(url, headers=self._headers(), method="GET")
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, list) else []
        except Exception as exc:  # noqa: BLE001
            self._note_error(exc)
            return []


# ====================================================================
# GESTOR PRINCIPAL DEL HISTORIAL SEMANAL
# ====================================================================
class WeeklyHistoryManager:
    """Calcula, guarda y reinicia ciclos semanales de productividad."""

    def __init__(
        self,
        sync_engine,
        config: Optional[Dict[str, Any]] = None,
        data_dir: Optional[str] = None,
    ):
        self.engine = sync_engine
        self.config = config or {}
        cfg = self.config.get("weekly", {}) or {}

        self.user_id = str(cfg.get("user_id") or DEFAULT_USER_ID)
        self.xp_per_task = int(cfg.get("xp_per_task") or DEFAULT_XP_PER_TASK)
        self.xp_per_habit = int(cfg.get("xp_per_habit") or DEFAULT_XP_PER_HABIT)
        self.xp_per_level = int(cfg.get("xp_per_level") or DEFAULT_XP_PER_LEVEL)
        self.auto_close_enabled = bool(cfg.get("auto_close_enabled", True))

        raw_dir = data_dir or cfg.get("data_dir") or "data"
        path = Path(str(raw_dir)).expanduser()
        self.data_dir = path if path.is_absolute() else (BASE_DIR / path)
        self.history_file = self.data_dir / "weekly_history.json"
        self.state_file = self.data_dir / "weekly_state.json"
        self.lock = threading.RLock()
        self.supabase = SupabaseMirror(self.config.get("supabase", {}) or {})
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Persistencia JSON
    # ------------------------------------------------------------------
    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    if default is None or isinstance(data, type(default)):
                        return data
        except Exception as exc:  # noqa: BLE001
            print(f"[WEEKLY] No se pudo leer {path.name}: {exc}")
        return default

    @staticmethod
    def _write_json(path: Path, data: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        temp.replace(path)

    def _load_state(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.state_file, None)

    def _save_state(self, state: Dict[str, Any]):
        state["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._write_json(self.state_file, state)

    def _load_records(self) -> List[Dict[str, Any]]:
        data = self._read_json(self.history_file, {"records": []})
        records = data.get("records", []) if isinstance(data, dict) else []
        return records if isinstance(records, list) else []

    def _save_records(self, records: List[Dict[str, Any]]):
        self._write_json(
            self.history_file,
            {
                "version": 1,
                "user_id": self.user_id,
                "records": records,
            },
        )

    # ------------------------------------------------------------------
    # Recolección de tareas desde la bóveda de Obsidian
    # ------------------------------------------------------------------
    def collect_snapshot(self) -> List[Dict[str, Any]]:
        """Devuelve todas las tareas actuales con claves estables."""
        tasks: List[Dict[str, Any]] = []

        try:
            studies = self.engine.get_studies_data()
        except Exception as exc:  # noqa: BLE001
            print(f"[WEEKLY] No se pudieron leer estudios: {exc}")
            studies = {}

        for track_key, track in (studies or {}).items():
            track_title = track.get("title") or track_key
            for section in track.get("sections", []) or []:
                section_title = section.get("title") or ""
                for task in section.get("tasks", []) or []:
                    raw = task.get("raw") or task.get("text") or ""
                    tasks.append(
                        {
                            "key": clean_task_key("estudios", track_key, raw),
                            "module": "estudios",
                            "module_label": track_title,
                            "scope": section_title,
                            "text": task.get("text") or raw,
                            "completed": bool(task.get("completed")),
                        }
                    )

        try:
            workshop = self.engine.get_workshop_tasks()
        except Exception as exc:  # noqa: BLE001
            print(f"[WEEKLY] No se pudo leer Rygon Studio: {exc}")
            workshop = []

        for category in workshop or []:
            category_title = category.get("category") or "Taller"
            for task in category.get("tasks", []) or []:
                raw = task.get("raw") or task.get("text") or ""
                tasks.append(
                    {
                        "key": clean_task_key("rygon", category_title, raw),
                        "module": "rygon",
                        "module_label": category_title,
                        "scope": category_title,
                        "text": task.get("text") or raw,
                        "completed": bool(task.get("completed")),
                    }
                )

        try:
            habits_data = self.engine.get_habits()
        except Exception as exc:  # noqa: BLE001
            print(f"[WEEKLY] No se pudieron leer hábitos: {exc}")
            habits_data = {}

        for habit in (habits_data or {}).get("habits", []) or []:
            raw = habit.get("raw") or habit.get("text") or ""
            tasks.append(
                {
                    "key": clean_task_key("rutinas", "diario", raw),
                    "module": "rutinas",
                    "module_label": "Hábitos diarios",
                    "scope": "diario",
                    "text": habit.get("text") or raw,
                    "completed": bool(habit.get("completed")),
                }
            )

        return tasks

    def _xp_for_task(self, task: Dict[str, Any]) -> int:
        return self.xp_per_habit if task.get("module") == "rutinas" else self.xp_per_task

    def _lifetime_xp_from_snapshot(self, snapshot: List[Dict[str, Any]]) -> int:
        seen: Set[str] = set()
        total = 0
        for task in snapshot:
            key = task.get("key")
            if not key or key in seen:
                continue
            seen.add(key)
            if task.get("completed"):
                total += self._xp_for_task(task)
        return total

    # ------------------------------------------------------------------
    # Cálculo del rendimiento semanal
    # ------------------------------------------------------------------
    def _aggregate(
        self,
        snapshot: List[Dict[str, Any]],
        baseline_completed: Set[str],
    ) -> Dict[str, Any]:
        """
        Calcula las métricas de la semana.

        Lógica de la línea base:
          - Las tareas que YA estaban completadas al inicio del ciclo no
            inflan la XP semanal.
          - Si una tarea de la línea base se desmarca, vuelve a entrar al
            universo semanal como pendiente.
          - Las tareas nuevas también entran automáticamente.
        """
        current: Dict[str, Dict[str, Any]] = {}
        for task in snapshot:
            key = task.get("key")
            if not key:
                continue
            if key not in current:
                current[key] = dict(task)
            else:
                current[key]["completed"] = (
                    current[key].get("completed") or task.get("completed")
                )

        effective_baseline = {
            key
            for key in baseline_completed
            if key in current and current[key].get("completed")
        }

        weekly_tasks = [
            task for key, task in current.items() if key not in effective_baseline
        ]

        total = len(weekly_tasks)
        completed = sum(1 for task in weekly_tasks if task.get("completed"))
        pending = total - completed
        effectiveness = round((completed / total) * 100, 2) if total else 0.0

        breakdown: Dict[str, Dict[str, Any]] = {
            module: {
                "label": label,
                "total": 0,
                "completed": 0,
                "xp": 0,
                "effectiveness": 0.0,
            }
            for module, label in MODULE_LABELS.items()
        }

        for task in weekly_tasks:
            module = task.get("module") or "estudios"
            bucket = breakdown.setdefault(
                module,
                {
                    "label": MODULE_LABELS.get(module, module.title()),
                    "total": 0,
                    "completed": 0,
                    "xp": 0,
                    "effectiveness": 0.0,
                },
            )
            bucket["total"] += 1
            if task.get("completed"):
                bucket["completed"] += 1
                bucket["xp"] += self._xp_for_task(task)

        for bucket in breakdown.values():
            bucket["effectiveness"] = (
                round((bucket["completed"] / bucket["total"]) * 100, 2)
                if bucket["total"]
                else 0.0
            )

        xp_earned = sum(bucket["xp"] for bucket in breakdown.values())
        vault_total = len(current)
        vault_completed = sum(
            1 for task in current.values() if task.get("completed")
        )
        vault_effectiveness = (
            round((vault_completed / vault_total) * 100, 2) if vault_total else 0.0
        )

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "xp_earned": xp_earned,
            "effectiveness_percentage": effectiveness,
            "breakdown": breakdown,
            "vault": {
                "total": vault_total,
                "completed": vault_completed,
                "pending": vault_total - vault_completed,
                "effectiveness": vault_effectiveness,
            },
        }

    # ------------------------------------------------------------------
    # Estado / ciclo actual
    # ------------------------------------------------------------------
    def _initialize_state(self, today: date) -> Dict[str, Any]:
        snapshot = self.collect_snapshot()
        baseline = sorted(
            {task["key"] for task in snapshot if task.get("completed")}
        )
        now = datetime.now().isoformat(timespec="seconds")
        state = {
            "version": 1,
            "user_id": self.user_id,
            "period_start": monday_of(today).isoformat(),
            "baseline_completed": baseline,
            "lifetime_xp": self._lifetime_xp_from_snapshot(snapshot),
            "acknowledged": [],
            "created_at": now,
            "updated_at": now,
        }
        self._save_state(state)
        return state

    def _current_state(self, today: date) -> Dict[str, Any]:
        state = self._load_state()
        if not state:
            state = self._initialize_state(today)
        if not state.get("period_start"):
            state["period_start"] = monday_of(today).isoformat()
            self._save_state(state)
        return state

    @staticmethod
    def _period_info(period_start: date, today: date) -> Dict[str, Any]:
        nominal_end = period_start + timedelta(days=6)
        days_remaining = (nominal_end - today).days
        return {
            "start": period_start.isoformat(),
            "end": nominal_end.isoformat(),
            "week_number": period_start.isocalendar().week,
            "year": period_start.isocalendar().year,
            "days_remaining": max(0, days_remaining),
            "is_overdue": today > nominal_end,
            "today": today.isoformat(),
        }

    def _lifetime_level(self, lifetime_xp: int) -> int:
        return (max(0, lifetime_xp) // max(1, self.xp_per_level)) + 1

    def maybe_auto_close(self, now: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """Cierra automáticamente el ciclo si ya pasó el domingo."""
        if not self.auto_close_enabled:
            return None

        today = now or date.today()
        with self.lock:
            state = self._load_state()
            if not state:
                self._initialize_state(today)
                return None

            period_start = safe_date(state.get("period_start"), monday_of(today))
            nominal_end = period_start + timedelta(days=6)
            if today > nominal_end:
                return self._close_locked(
                    today, status="completed", source="auto", force=False
                )
        return None

    def get_current_week(
        self,
        now: Optional[date] = None,
        allow_auto_close: bool = True,
    ) -> Dict[str, Any]:
        """Vista previa del ciclo activo (sin guardar historial)."""
        today = now or date.today()
        with self.lock:
            auto_closed = None
            if allow_auto_close:
                auto_closed = self.maybe_auto_close(today)

            state = self._current_state(today)
            period_start = safe_date(state.get("period_start"), monday_of(today))
            snapshot = self.collect_snapshot()
            metrics = self._aggregate(
                snapshot, set(state.get("baseline_completed", []))
            )
            lifetime_xp = int(state.get("lifetime_xp") or 0)

            return {
                "period": self._period_info(period_start, today),
                "metrics": metrics,
                "lifetime_xp": lifetime_xp,
                "lifetime_level": self._lifetime_level(lifetime_xp),
                "lifetime_level_xp": lifetime_xp % max(1, self.xp_per_level),
                "xp_per_level": self.xp_per_level,
                "xp_per_task": self.xp_per_task,
                "xp_per_habit": self.xp_per_habit,
                "auto_close_enabled": self.auto_close_enabled,
                "can_close": True,
                "last_closed": auto_closed.get("record") if auto_closed else None,
                "supabase": {
                    "enabled": self.supabase.enabled,
                    "configured": self.supabase.configured,
                },
            }

    # ------------------------------------------------------------------
    # Cierre de semana
    # ------------------------------------------------------------------
    def _close_locked(
        self,
        today: date,
        status: str,
        source: str,
        force: bool,
    ) -> Dict[str, Any]:
        state = self._current_state(today)
        period_start = safe_date(state.get("period_start"), monday_of(today))
        nominal_end = period_start + timedelta(days=6)

        # Evita dobles cierres consecutivos: si el ciclo nuevo aún no
        # comienza (p. ej. cierre manual hoy y otro clic inmediato), no se
        # genera un registro vacío para el ciclo futuro.
        if today < period_start:
            return {
                "closed": False,
                "reason": "already_closed",
                "record": None,
                "metrics": None,
            }

        if source == "auto":
            period_end = nominal_end
        else:
            period_end = min(today, nominal_end)
            if period_end < period_start:
                period_end = period_start

        snapshot = self.collect_snapshot()
        metrics = self._aggregate(
            snapshot, set(state.get("baseline_completed", []))
        )
        records = self._load_records()

        existing = next(
            (
                record
                for record in records
                if record.get("user_id") == self.user_id
                and record.get("week_start_date") == period_start.isoformat()
            ),
            None,
        )

        if existing and not force:
            return {
                "closed": False,
                "reason": "already_closed",
                "record": existing,
                "metrics": metrics,
            }

        if (
            metrics["total_tasks"] == 0
            and metrics["completed_tasks"] == 0
            and not force
        ):
            return {
                "closed": False,
                "reason": "empty_week",
                "record": None,
                "metrics": metrics,
            }

        lifetime_xp = int(state.get("lifetime_xp") or 0)
        if existing and force:
            lifetime_xp = max(
                0, lifetime_xp - int(existing.get("xp_earned") or 0)
            )
            records = [
                record
                for record in records
                if record.get("id") != existing.get("id")
            ]

        record = {
            "id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "week_start_date": period_start.isoformat(),
            "week_end_date": period_end.isoformat(),
            "week_number": period_start.isocalendar().week,
            "year": period_start.isocalendar().year,
            "total_tasks": metrics["total_tasks"],
            "completed_tasks": metrics["completed_tasks"],
            "pending_tasks": metrics["pending_tasks"],
            "xp_earned": metrics["xp_earned"],
            "effectiveness_percentage": metrics["effectiveness_percentage"],
            "status": status if status in ("completed", "reset") else "completed",
            "breakdown": metrics["breakdown"],
            "vault": metrics["vault"],
            "source": source,
            "closed_at": datetime.now().isoformat(timespec="seconds"),
            "synced": False,
        }

        records.append(record)
        state["lifetime_xp"] = lifetime_xp + metrics["xp_earned"]

        new_start = period_end + timedelta(days=1)
        if source == "auto":
            new_start = max(new_start, monday_of(today))
        state["period_start"] = new_start.isoformat()
        state["baseline_completed"] = sorted(
            {task["key"] for task in snapshot if task.get("completed")}
        )
        state["last_closed_id"] = record["id"]
        state["acknowledged"] = [
            record_id
            for record_id in state.get("acknowledged", [])
            if record_id != record["id"]
        ]

        self._save_records(records)
        self._save_state(state)

        record["synced"] = self.supabase.upsert(record)
        if record["synced"]:
            self._save_records(records)

        return {
            "closed": True,
            "reason": "closed",
            "record": record,
            "metrics": metrics,
            "lifetime_xp": state["lifetime_xp"],
            "lifetime_level": self._lifetime_level(state["lifetime_xp"]),
        }

    def close_week(
        self,
        status: str = "completed",
        force: bool = False,
        source: str = "manual",
        now: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Cierra el ciclo actual y reinicia el contador semanal."""
        if status not in ("completed", "reset"):
            status = "completed"
        today = now or date.today()
        with self.lock:
            return self._close_locked(
                today, status=status, source=source, force=force
            )

    # ------------------------------------------------------------------
    # Historial, acuses y sincronización
    # ------------------------------------------------------------------
    @staticmethod
    def _aggregates(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {
                "total_weeks": 0,
                "total_xp": 0,
                "avg_effectiveness": 0.0,
                "best_week": None,
                "total_completed": 0,
                "total_tasks": 0,
                "completed_weeks": 0,
                "reset_weeks": 0,
            }

        total_xp = sum(int(record.get("xp_earned") or 0) for record in records)
        avg_effectiveness = round(
            sum(
                float(record.get("effectiveness_percentage") or 0)
                for record in records
            )
            / len(records),
            2,
        )
        best_week = max(
            records,
            key=lambda record: float(
                record.get("effectiveness_percentage") or 0
            ),
        )
        return {
            "total_weeks": len(records),
            "total_xp": total_xp,
            "avg_effectiveness": avg_effectiveness,
            "best_week": best_week,
            "total_completed": sum(
                int(record.get("completed_tasks") or 0) for record in records
            ),
            "total_tasks": sum(
                int(record.get("total_tasks") or 0) for record in records
            ),
            "completed_weeks": sum(
                1 for record in records if record.get("status") == "completed"
            ),
            "reset_weeks": sum(
                1 for record in records if record.get("status") == "reset"
            ),
        }

    def _normalize_remote(self, record: Dict[str, Any]) -> Dict[str, Any]:
        total = int(record.get("total_tasks") or 0)
        completed = int(record.get("completed_tasks") or 0)
        return {
            "id": record.get("id"),
            "user_id": record.get("user_id") or self.user_id,
            "week_start_date": record.get("week_start_date"),
            "week_end_date": record.get("week_end_date"),
            "week_number": (
                safe_date(record.get("week_start_date"), date.today())
                .isocalendar()
                .week
            ),
            "year": (
                safe_date(record.get("week_start_date"), date.today())
                .isocalendar()
                .year
            ),
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": max(0, total - completed),
            "xp_earned": int(record.get("xp_earned") or 0),
            "effectiveness_percentage": float(
                record.get("effectiveness_percentage") or 0
            ),
            "status": record.get("status") or "completed",
            "breakdown": record.get("breakdown") or {},
            "vault": record.get("vault") or {},
            "source": record.get("source") or "supabase",
            "closed_at": record.get("closed_at"),
            "synced": True,
        }

    def _merge_remote(
        self,
        records: List[Dict[str, Any]],
        remote_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for record in records:
            key = (
                str(record.get("user_id") or self.user_id),
                str(record.get("week_start_date") or ""),
            )
            merged[key] = record
        for record in remote_records:
            normalized = self._normalize_remote(record)
            key = (
                str(normalized.get("user_id") or self.user_id),
                str(normalized.get("week_start_date") or ""),
            )
            if key not in merged:
                merged[key] = normalized
        return list(merged.values())

    def get_history(
        self,
        merge_remote: bool = False,
        now: Optional[date] = None,
    ) -> Dict[str, Any]:
        today = now or date.today()
        with self.lock:
            self.maybe_auto_close(today)
            records = self._load_records()

            if merge_remote:
                remote_records = self.supabase.fetch_all()
                if remote_records:
                    records = self._merge_remote(records, remote_records)
                    self._save_records(records)

            records.sort(
                key=lambda record: (
                    str(record.get("week_start_date") or ""),
                    str(record.get("closed_at") or ""),
                ),
                reverse=True,
            )
            aggregates = self._aggregates(records)
            state = self._load_state() or {}
            acknowledged = set(state.get("acknowledged", []))
            pending = next(
                (
                    record
                    for record in records
                    if record.get("id") not in acknowledged
                ),
                None,
            )

            return {
                "records": records,
                "aggregates": aggregates,
                "pending_summary": pending,
                "supabase": {
                    "enabled": self.supabase.enabled,
                    "configured": self.supabase.configured,
                    "synced_count": sum(
                        1 for record in records if record.get("synced")
                    ),
                    "pending_count": sum(
                        1 for record in records if not record.get("synced")
                    ),
                },
            }

    def acknowledge(self, record_id: Optional[str]) -> Dict[str, Any]:
        if not record_id:
            return {"success": False, "error": "id requerido"}
        with self.lock:
            state = self._current_state(date.today())
            acknowledged = set(state.get("acknowledged", []))
            acknowledged.add(str(record_id))
            state["acknowledged"] = sorted(acknowledged)
            self._save_state(state)
            return {"success": True, "acknowledged": record_id}

    def sync_pending(self) -> Dict[str, Any]:
        with self.lock:
            if not self.supabase.configured:
                return {
                    "success": False,
                    "configured": False,
                    "synced": 0,
                    "pending": len(self._load_records()),
                    "message": (
                        "Supabase no está configurado. Define SUPABASE_URL y "
                        "SUPABASE_SERVICE_ROLE_KEY (o SUPABASE_ANON_KEY)."
                    ),
                }

            records = self._load_records()
            synced = 0
            for record in records:
                if not record.get("synced") and self.supabase.upsert(record):
                    record["synced"] = True
                    synced += 1

            if synced:
                self._save_records(records)

            pending = sum(1 for record in records if not record.get("synced"))
            if synced:
                message = f"{synced} registro(s) sincronizado(s)."
            elif pending:
                message = (
                    f"{pending} registro(s) pendientes. Revisa la tabla "
                    "weekly_history y las políticas RLS de Supabase."
                )
            else:
                message = "No había registros pendientes."
            return {
                "success": True,
                "configured": True,
                "synced": synced,
                "pending": pending,
                "message": message,
            }
