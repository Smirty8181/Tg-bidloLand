# Запуск БыдлоЛенд через Cloudflare Quick Tunnel
# Использование: powershell -ExecutionPolicy Bypass -File scripts\start_tunnel.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

New-Item -ItemType Directory -Force -Path logs, data | Out-Null

$cloudflared = Join-Path $Root "tools\cloudflared.exe"
if (-not (Test-Path $cloudflared)) {
    Write-Host "Скачиваю cloudflared..."
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "tools") | Out-Null
    curl.exe -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -o $cloudflared
}

# Остановить старые процессы на 8080
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

Write-Host "[1/3] Backend :8080"
Start-Process -WindowStyle Minimized python -ArgumentList "-m","uvicorn","backend.main:app","--host","127.0.0.1","--port","8080" -WorkingDirectory $Root -RedirectStandardOutput (Join-Path $Root "logs\backend.out.log") -RedirectStandardError (Join-Path $Root "logs\backend.err.log")
Start-Sleep -Seconds 3

Write-Host "[2/3] Cloudflare tunnel"
$tunnelLog = Join-Path $Root "logs\tunnel.log"
if (Test-Path $tunnelLog) { Remove-Item $tunnelLog -Force }
Start-Process -WindowStyle Minimized $cloudflared -ArgumentList "tunnel","--url","http://127.0.0.1:8080","--no-autoupdate" -WorkingDirectory $Root -RedirectStandardOutput $tunnelLog -RedirectStandardError $tunnelLog

$tunnelUrl = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    if (Test-Path $tunnelLog) {
        $match = Select-String -Path $tunnelLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches |
            ForEach-Object { $_.Matches } | Select-Object -Last 1
        if ($match) { $tunnelUrl = $match.Value; break }
    }
}
if (-not $tunnelUrl) { throw "Не удалось получить URL туннеля. См. logs\tunnel.log" }

Write-Host "Tunnel: $tunnelUrl"
$envPath = Join-Path $Root ".env"
(Get-Content $envPath -Raw) -replace "WEBAPP_URL=.*", "WEBAPP_URL=$tunnelUrl" | Set-Content $envPath -NoNewline

Write-Host "[3/3] Telegram bot"
Start-Process -WindowStyle Minimized python -ArgumentList "-m","bot.main" -WorkingDirectory $Root -RedirectStandardOutput (Join-Path $Root "logs\bot.out.log") -RedirectStandardError (Join-Path $Root "logs\bot.err.log")

Write-Host ""
Write-Host "Done!"
Write-Host "  Mini App: $tunnelUrl"
Write-Host "  API:      http://127.0.0.1:8080"
Write-Host "  Logs:     logs\"
