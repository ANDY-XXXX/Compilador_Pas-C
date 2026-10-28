#!/usr/bin/env bash
# Instalador - Compilador Equipo 6 (Ubuntu / Debian)
# Vive en INSTALL/ y trabaja sobre INSTALL/.
set -e

cd "$(dirname "$0")"

echo "==> Proyecto: $(pwd)"

if [ ! -f "main.py" ]; then
    echo "ERROR: no se encontró main.py en $(pwd)"
    echo "Este script debe estar en la carpeta INSTALL/ del proyecto."
    exit 1
fi

echo "==> 1/3 Paquetes del sistema (se pedirá la contraseña de administrador)"
sudo apt update
sudo apt install -y python3 python3-venv python3-pip flex gcc \
    libegl1 libgl1 libxcb-cursor0 libxkbcommon-x11-0

echo "==> 2/3 Entorno virtual y dependencias"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "==> 3/3 Verificación"
flex --version
gcc --version | head -n 1
.venv/bin/python -c "import PyQt6; print('PyQt6 OK')"

echo
echo "Instalación terminada. Para abrir la aplicación:"
echo "    ./INSTALL/ejecutar_linux.sh"