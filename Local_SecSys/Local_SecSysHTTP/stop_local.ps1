# =========================================================
# Local Security System (HTTP Version) — Stop Script
# =========================================================

Write-Host "Stopping Local HTTP Security System processes (ports 3000, 5000, 8000)..." -ForegroundColor Yellow

$ports = @(3000, 5000, 8000)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "[STOPPED] Process ID $procId on port $port" -ForegroundColor Green
            } catch {}
        }
    } else {
        Write-Host "[OK] Port $port is already clear." -ForegroundColor Gray
    }
}

Write-Host "All HTTP system services stopped." -ForegroundColor Green
