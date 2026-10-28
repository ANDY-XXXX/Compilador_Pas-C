#!/usr/bin/env bash
# Lanzador - Compilador Equipo 6 (Ubuntu / Debian)
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "Primero ejecuta: ./INSTALL/instalar_linux.sh"
    exit 1
fi

.venv/bin/python main.py