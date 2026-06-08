@echo off
cd /d "%~dp0backend"
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Arrancando servidor...
rem Las credenciales se cargan desde backend/.env automáticamente
python server.py
pause
