@echo off
setlocal
cd /d "%~dp0.."

if not exist "logs" mkdir logs
if not exist "data" mkdir data

echo [1/3] Starting backend on :8080...
start "BydloLand Backend" /MIN cmd /c "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080 >> logs\backend.out.log 2>&1"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Cloudflare tunnel...
if exist "tools\cloudflared.exe" (
  start "BydloLand Tunnel" /MIN cmd /c "tools\cloudflared.exe tunnel --url http://127.0.0.1:8080 --no-autoupdate >> logs\tunnel.log 2>&1"
) else (
  echo cloudflared not found in tools\cloudflared.exe
  exit /b 1
)

echo Waiting for tunnel URL...
set TUNNEL_URL=
for /L %%i in (1,1,30) do (
  timeout /t 2 /nobreak >nul
  for /f "usebackq tokens=*" %%u in (`powershell -NoProfile -Command "(Select-String -Path 'logs\tunnel.log' -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -AllMatches | ForEach-Object { $_.Matches } | Select-Object -Last 1 -ExpandProperty Value)"`) do set TUNNEL_URL=%%u
  if defined TUNNEL_URL goto :found
)
:found
if not defined TUNNEL_URL (
  echo Could not detect tunnel URL. Check logs\tunnel.log
  exit /b 1
)

echo Tunnel: %TUNNEL_URL%
powershell -NoProfile -Command "$p='.env'; $c=Get-Content $p -Raw; $c=$c -replace 'WEBAPP_URL=.*','WEBAPP_URL=%TUNNEL_URL%'; Set-Content $p $c -NoNewline"

echo [3/3] Starting Telegram bot...
start "BydloLand Bot" /MIN cmd /c "python -m bot.main >> logs\bot.out.log 2>&1"

echo.
echo Ready:
echo   Mini App: %TUNNEL_URL%
echo   Local API: http://127.0.0.1:8080
echo   Logs: logs\
endlocal
