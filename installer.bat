@echo off
SETLOCAL ENABLEEXTENSIONS

echo ========================================
echo Instalando Python (modo usuario, sin admin)...
echo ========================================

REM --- Ruta al instalador de Python ---
SET PYTHON_INSTALLER=python-3.11.6-amd64.exe

REM --- Descargar Python si no existe ---
IF NOT EXIST %PYTHON_INSTALLER% (
    echo Descargando Python...
    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe -OutFile %PYTHON_INSTALLER%"
)

REM --- Instalar Python en modo usuario (NO admin) ---
%PYTHON_INSTALLER% /quiet PrependPath=1 Include_test=0

REM --- Agregar Python al PATH temporalmente ---
SET PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%LOCALAPPDATA%\Programs\Python\Python311\

echo ========================================
echo Instalando dependencias Python...
echo ========================================
python -m pip install --upgrade pip

IF EXIST requirements.txt (
    python -m pip install -r requirements.txt
) ELSE (
    echo ERROR: requirements.txt no encontrado.
    pause
    exit /b
)

echo ========================================
echo wkhtmltopdf portable listo para usar.
echo ========================================

REM --- Agregar wkhtmltopdf portable al PATH temporalmente ---
SET PATH=%PATH%;%CD%\wkhtmltopdf_portable\bin\

echo ========================================
echo Entorno configurado correctamente.
pause