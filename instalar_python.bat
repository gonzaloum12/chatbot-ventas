@echo off
echo Descargando Python 3.12 desde python.org...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
echo Instalando Python (puede tardar un minuto)...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
echo.
echo Listo. Cierra esta ventana y abre una nueva CMD para usar Python.
pause
