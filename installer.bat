@echo off
SETLOCAL ENABLEEXTENSIONS

echo ========================================
echo Instalando Python y dependencias...
echo ========================================

REM --- Ruta del instalador de Python (ajústalo si lo tienes en la carpeta) ---
SET PYTHON_INSTALLER=python-3.11.6-amd64.exe

REM --- Descargar Python si no existe ---
IF NOT EXIST %PYTHON_INSTALLER% (
    echo Descargando Python 3...
    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe -OutFile %PYTHON_INSTALLER%"
)

REM --- Instalar Python silenciosamente ---
%PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

REM --- Actualizar PATH para la sesión actual ---
SET PATH=%PATH%;C:\Python311\Scripts\;C:\Python311\

echo ========================================
echo Instalando dependencias Python (requirements.txt)...
echo ========================================
python -m pip install --upgrade pip

IF EXIST requirements.txt (
    python -m pip install -r requirements.txt
) ELSE (
    echo requirements.txt no encontrado.
    pause
    exit /b
)

echo ========================================
echo Instalando wkhtmltopdf...
echo ========================================

REM --- Ruta del instalador wkhtmltopdf ---
SET WKHTML_INSTALLER=wkhtmltox-0.12.6-1.msvc2015-win64.exe

REM --- Descargar wkhtmltopdf si no existe ---
IF NOT EXIST %WKHTML_INSTALLER% (
    echo Descargando wkhtmltopdf...
    powershell -Command "Invoke-WebRequest https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe -OutFile %WKHTML_INSTALLER%"
)

REM --- Instalar wkhtmltopdf silenciosamente ---
%WKHTML_INSTALLER% /S

REM --- Agregar wkhtmltopdf al PATH para la sesión actual ---
SET PATH=%PATH%;C:\Program Files\wkhtmltopdf\bin\

echo ========================================
echo Entorno configurado correctamente.
pause