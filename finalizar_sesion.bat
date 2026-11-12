@echo off
TITLE ERP Django - Guardando Sesion
COLOR 0E

:: ── 1. RUTAS ──────────────────────────────────────────────────────────────
SET PC_WORK=C:\Temp_Workspace_ERP
SET USB_PATH=%~d0\

echo ======================================================
echo  ERP DJANGO :: PC ^-^> USB (RESPALDO)
echo ======================================================

:: ── 2. VERIFICAR QUE EXISTE EL TALLER ────────────────────────────────────
if not exist "%PC_WORK%" (
    echo [ERROR] No existe %PC_WORK%[cite: 1]
    echo Ejecuta primero iniciar_sesion.bat[cite: 1]
    pause & exit /b 1
)

:: ── 3. LIBERAR PROCESOS EN SEGUNDO PLANO ──────────────────────────────────
taskkill /FI "IMAGENAME eq python.exe" /F >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── 4. SINCRONIZAR PC → USB (solo archivos nuevos o modificados) ──────────
echo Guardando cambios en la USB...[cite: 1]

:: Excluir el entorno virtual temporalmente
echo \env_erp\ > "%PC_WORK%\exclude_temp.txt"

:: Copia silenciosa de todos los cambios de PC a USB
xcopy /s /e /y /d /exclude:%PC_WORK%\exclude_temp.txt "%PC_WORK%" "%USB_PATH%WorkSpace_ERP" >nul 2>&1

set COPY_STATUS=%ERRORLEVEL%
if exist "%PC_WORK%\exclude_temp.txt" del "%PC_WORK%\exclude_temp.txt"

echo.
echo ======================================================
if %COPY_STATUS% LEQ 1 (
    echo  RESPALDO COMPLETADO.[cite: 1]
    echo  Guardado en: %USB_PATH%WorkSpace_ERP[cite: 1]
    echo  Incluye: codigo .py, templates, db.sqlite3, .git[cite: 1]
    echo ======================================================
    echo  Es seguro retirar la USB.[cite: 1]
) else (
    echo  [ERROR] Ocurrio un fallo al guardar en la USB.
    echo  Verifica que la memoria este bien conectada.
)
echo ======================================================
cmd /k "echo."