# =========================================================
# SecSysMqtt — Shutdown Script
# =========================================================

Write-Host "Stopping SecSysMqtt services on ports 3000, 5000, 8000..." -ForegroundColor Yellow
foreach ($port in @(3000, 5000, 8000)) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "  Stopped process $procId on port $port" -ForegroundColor Green
            } catch {}
        }
    } else {
        Write-Host "  Port $port is already free." -ForegroundColor Gray
    }
}
Write-Host "All SecSysMqtt services stopped." -ForegroundColor Green
Write-Host "Note: The Mosquitto broker (port 1883) is a Windows service and was NOT stopped." -ForegroundColor Gray
