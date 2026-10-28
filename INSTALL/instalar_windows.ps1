# Instalador automatico - Compilador Equipo 6 (Windows)
# Instala Python, MSYS2 (Flex y GCC), crea el entorno virtual e instala PyQt6.
# Se puede ejecutar varias veces: omite lo que ya esta instalado.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$msys = "C:\msys64"
$bash = "$msys\usr\bin\bash.exe"

function Paso($texto) {
    Write-Host ""
    Write-Host "==> $texto" -ForegroundColor Cyan
}

function Actualizar-Path {
    $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $u = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$m;$u"
}

function Python-Listo {
    try {
        $v = (& python --version 2>&1 | Out-String)
        if ($LASTEXITCODE -ne 0) { return $false }
        if ($v -match "Python 3\.(\d+)") { return ([int]$Matches[1] -ge 10) }
    } catch { }
    return $false
}

try {
    if (-not (Test-Path "requirements.txt")) {
        throw "No se encontro requirements.txt. Ejecuta este instalador desde la carpeta del proyecto."
    }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "No se encontro 'winget'. Instala 'Instalador de aplicaciones' desde Microsoft Store o usa la instalacion manual (Anexo A de la guia)."
    }

    Paso "1/4 Python"
    if (-not (Python-Listo)) {
        winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -notin @(0, 3010)) { throw "No se pudo instalar Python con winget." }
        Actualizar-Path
    }
    if (-not (Python-Listo)) {
        throw "Python aun no esta disponible. Cierra esta ventana y vuelve a ejecutar instalar_windows.bat."
    }
    Write-Host "Python listo."

    Paso "2/4 MSYS2 (Flex y GCC)"
    if (-not (Test-Path $bash)) {
        winget install -e --id MSYS2.MSYS2 --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -notin @(0, 3010)) { throw "No se pudo instalar MSYS2 con winget." }
    }
    if (-not (Test-Path $bash)) {
        throw "MSYS2 no quedo instalado en C:\msys64. Instalalo desde msys2.org (ruta por defecto) y vuelve a ejecutar este instalador."
    }
    if (-not ((Test-Path "$msys\ucrt64\bin\gcc.exe") -and (Test-Path "$msys\usr\bin\flex.exe"))) {
        & $bash -lc "pacman -Syu --noconfirm"
        if ($LASTEXITCODE -ne 0) { throw "Fallo la actualizacion de MSYS2. Revisa el mensaje de pacman. Si solicita cerrar las terminales de MSYS2, cierralas y vuelve a ejecutar instalar_windows.bat." }
        & $bash -lc "pacman -Syu --noconfirm"
        if ($LASTEXITCODE -ne 0) { throw "Fallo la actualizacion de MSYS2. Revisa el mensaje de pacman. Si solicita cerrar las terminales de MSYS2, cierralas y vuelve a ejecutar instalar_windows.bat." }
        & $bash -lc "pacman -S --needed --noconfirm m4 mingw-w64-ucrt-x86_64-toolchain flex"
        if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar Flex y GCC. Revisa el mensaje de pacman que aparece arriba." }
    }
    if (-not (Test-Path "$msys\usr\bin\flex.exe")) {
        throw "No se encontro Flex en C:\msys64\usr\bin\flex.exe."
    }
    if (-not (Test-Path "$msys\ucrt64\bin\gcc.exe")) {
        throw "No se encontro GCC en C:\msys64\ucrt64\bin\gcc.exe."
    }
    Write-Host "MSYS2, Flex y GCC instalados; se verificaran en el paso 4."

    Paso "3/4 Entorno virtual y dependencias"
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual .venv." }
    }
    & ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "No se pudo actualizar pip en el entorno virtual." }
    & ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de requirements.txt." }

    Paso "4/4 Verificacion"
    $env:Path = "$msys\ucrt64\bin;" + $env:Path + ";$msys\usr\bin"
    & "$msys\usr\bin\flex.exe" --version
    if ($LASTEXITCODE -ne 0) { throw "Flex no responde." }
    & "$msys\ucrt64\bin\gcc.exe" --version
    if ($LASTEXITCODE -ne 0) { throw "GCC no responde." }
    & ".venv\Scripts\python.exe" -c "import PyQt6; print('PyQt6 OK')"
    if ($LASTEXITCODE -ne 0) { throw "PyQt6 no se instalo correctamente." }

    Write-Host ""
    Write-Host "Instalacion terminada. Para abrir la aplicacion usa ejecutar.bat" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
