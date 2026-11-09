#!/usr/bin/env bash
# ====================================================================
# THIAN-CORE // SCRIPT DE ARRANQUE PARA FEDORA LINUX
# ====================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "========================================================"
echo " 🕹️  INICIANDO THIAN-CORE WORKSTATION & OBSIDIAN HUB"
echo "========================================================"

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado en este sistema Fedora."
    exit 1
fi

# Comprobar si existe entorno virtual con FastAPI
if [ -f ".venv/bin/python" ] && .venv/bin/python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "⚡ Entorno virtual con FastAPI detectado. Iniciando con Uvicorn..."
    exec .venv/bin/uvicorn backend.main_fastapi:app --host 0.0.0.0 --port 8080 --reload
else
    echo "🚀 Iniciando con el servidor optimizado nativo de Python 3..."
    exec python3 app.py
fi
