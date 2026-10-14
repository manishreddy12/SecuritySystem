# =========================================================
# SecSysHTTP — Shutdown Script
# =========================================================

Write-Host "Stopping SecSysHTTP services on ports 3000, 5000, 8000..." -ForegroundColor Yellow
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
Write-Host "All SecSysHTTP services stopped." -ForegroundColor Green
