@echo off
setlocal
set "SITE=%~dp0"
if "%SITE:~-1%"=="\" set "SITE=%SITE:~0,-1%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$site=$env:SITE; if (-not (Test-NetConnection -ComputerName localhost -Port 8964 -InformationLevel Quiet)) { Start-Process -FilePath 'cmd.exe' -ArgumentList '/c npm run dev -- --port 8964' -WorkingDirectory $site -WindowStyle Minimized; Start-Sleep -Seconds 4 }; Start-Process 'http://localhost:8964/'"
