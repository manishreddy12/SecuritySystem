# =========================================================
# Local Security System (MQTT Version) — Stop Script
# =========================================================

Write-Host "Stopping Local MQTT Security System processes..." -ForegroundColor Yellow

# Stop ports 3000, 5000, 8000
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

# Stop any running python mqtt_worker processes
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like "*mqtt_worker.py*" } | ForEach-Object {
    try {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[STOPPED] MQTT Worker (PID $($_.ProcessId))" -ForegroundColor Green
    } catch {}
}

Write-Host "All MQTT system services stopped." -ForegroundColor Green
