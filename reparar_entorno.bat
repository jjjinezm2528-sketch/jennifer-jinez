@echo off
TITLE ERP Django - Reparar entorno virtual
COLOR 0E
:: Colocar este archivo junto a manage.py y ejecutarlo con doble clic.
cd /d "%~dp0"

if not exist "manage.py" (
    echo [ERROR] No encuentro manage.py en %CD%
    echo         Copia este archivo a la carpeta del proyecto.
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo [ERROR] No encuentro requirements.txt en %CD%
    pause
    exit /b 1
)

:: Detectar Python del sistema (python o py launcher)
SET PY=python
python --version >nul 2>&1
if errorlevel 1 SET PY=py -3
%PY% --version
if errorlevel 1 (
    echo [ERROR] No se encontro Python. Instalalo desde python.org
    pause
    exit /b 1
)

:: Si el entorno ya funciona, no tocarlo
if exist "env_erp\Scripts\python.exe" (
    "env_erp\Scripts\python.exe" -c "import django" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] El entorno env_erp ya tiene Django instalado.
        goto :verificar
    )
    echo Entorno danado o incompleto. Eliminando env_erp...
    rmdir /s /q "env_erp"
)

echo Creando entorno virtual env_erp...
%PY% -m venv env_erp
if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

echo Instalando dependencias, esto puede tardar unos minutos...
"env_erp\Scripts\python.exe" -m pip install --upgrade pip
"env_erp\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la instalacion. Copia el mensaje de error de arriba y mandalo.
    pause
    exit /b 1
)

:verificar
echo.
echo Verificando proyecto...
"env_erp\Scripts\python.exe" manage.py check
echo.
echo ======================================================
echo  LISTO. Para correr el servidor en PowerShell:
echo     .\env_erp\Scripts\Activate.ps1
echo     python manage.py runserver
echo.
echo  O sin activar nada:
echo     .\env_erp\Scripts\python.exe manage.py runserver
echo ======================================================
pause
