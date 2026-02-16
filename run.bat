@echo off
chcp 65001 >nul 2>nul
cd /d "%~dp0"

echo ==============================
echo  Chinese Vocab Generator
echo  http://localhost:8000
echo ==============================
echo.

:: Kill ALL python processes to free port
taskkill /IM python.exe /F >nul 2>nul
timeout /t 3 /nobreak >nul

:: Verify port is free
netstat -ano | findstr ":8000.*LISTENING" >nul 2>nul
if %errorlevel%==0 (
    echo ERROR: Port 8000 is still in use!
    echo Close all programs using port 8000 and try again.
    pause
    exit /b 1
)

:: Clear Python cache
for /d /r "app" %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"

echo Starting server...
echo.
C:\Python313\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
