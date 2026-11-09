import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "debug": True
    },
    "obsidian": {
        # Si tienes una bóveda existente de Obsidian, pon su ruta absoluta aquí:
        # Por defecto se utiliza la carpeta 'obsidian_vault' dentro del proyecto.
        "vault_path": str(BASE_DIR / "obsidian_vault"),
        "auto_sync_interval_seconds": 5,
        "create_if_missing": True
    },
    "app": {
        "title": "THIAN-CORE // RETRO WORKSTATION",
        "version": "1.0.0",
        "theme": "terminal-orange"
    }
}

CONFIG_FILE = BASE_DIR / "config.json"

def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                for k, v in user_cfg.items():
                    if isinstance(v, dict) and k in config:
                        config[k].update(v)
                    else:
                        config[k] = v
        except Exception as e:
            print(f"[CONFIG] Error cargando config.json: {e}. Usando valores por defecto.")
    else:
        save_config(config)
    
    # Permitir sobreescritura por variable de entorno OBSIDIAN_VAULT_PATH
    env_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_vault:
        config["obsidian"]["vault_path"] = os.path.abspath(os.path.expanduser(env_vault))
    else:
        config["obsidian"]["vault_path"] = os.path.abspath(os.path.expanduser(config["obsidian"]["vault_path"]))
        
    return config

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[CONFIG] Error guardando config.json: {e}")
