# =========================================================
# Local Security System (MQTT Version) — Local Launcher
# =========================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Starting Local MQTT Security System" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 0. Detect Python executable (use active venv, local .venv, or system python)
$pythonExe = "python"
if ($env:VIRTUAL_ENV -and (Test-Path "$env:VIRTUAL_ENV\Scripts\python.exe")) {
    $pythonExe = "$env:VIRTUAL_ENV\Scripts\python.exe"
    Write-Host "[OK] Using active virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Green
} elseif (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
    $pythonExe = "$ScriptDir\.venv\Scripts\python.exe"
    Write-Host "[OK] Using virtual environment: .venv" -ForegroundColor Green
} elseif (Test-Path "$ScriptDir\venv\Scripts\python.exe") {
    $pythonExe = "$ScriptDir\venv\Scripts\python.exe"
    Write-Host "[OK] Using virtual environment: venv" -ForegroundColor Green
} else {
    Write-Host "[INFO] Using system python" -ForegroundColor Gray
}

# 1. Clean up any stale processes from earlier runs
Write-Host "Cleaning up previous processes on ports 3000, 5000, 8000..." -ForegroundColor Gray
$ports = @(3000, 5000, 8000)
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*mqtt_worker.py*" } | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
}

# 2. Test MongoDB Connection (23017 or 27017)
$mongoPort = 23017
$mongoOk = $false
try {
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 23017 -WarningAction SilentlyContinue
    if ($conn.TcpTestSucceeded) {
        $mongoOk = $true
        $mongoPort = 23017
    }
} catch {}

if (-not $mongoOk) {
    try {
        $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -WarningAction SilentlyContinue
        if ($conn.TcpTestSucceeded) {
            $mongoOk = $true
            $mongoPort = 27017
        }
    } catch {}
}

if ($mongoOk) {
    Write-Host "[OK] MongoDB is running on port $mongoPort" -ForegroundColor Green
    $env:MONGO_URI = "mongodb://localhost:$mongoPort"
} else {
    Write-Host "[WARNING] Could not detect MongoDB on port 23017 or 27017." -ForegroundColor Yellow
}

# 3. Test Mosquitto MQTT Broker (Port 1883)
$mqttOk = $false
try {
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 1883 -WarningAction SilentlyContinue
    if ($conn.TcpTestSucceeded) {
        $mqttOk = $true
    }
} catch {}

if (-not $mqttOk) {
    $svc = Get-Service -Name *mosquitto* -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Host "Starting Mosquitto service..." -ForegroundColor Yellow
        Start-Service $svc.Name -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        $mqttOk = $true
    } else {
        Write-Host "[ACTION REQUIRED] Mosquitto MQTT broker is not running on port 1883." -ForegroundColor Red
        Write-Host "To install it, run in an Administrator PowerShell:" -ForegroundColor Yellow
        Write-Host "  winget install EclipseFoundation.Mosquitto" -ForegroundColor White
    }
} else {
    Write-Host "[OK] Mosquitto MQTT Broker is running on port 1883" -ForegroundColor Green
}

# 4. Seed Demo Data
Write-Host "`nSeeding demo data (Door1, user 'manish', PIN '1234')..." -ForegroundColor Cyan
try {
    Push-Location "$ScriptDir\Backend"
    & "$pythonExe" seed_data.py
    Pop-Location
} catch {
    Write-Host "[WARNING] Seeding returned an error: $_" -ForegroundColor Yellow
    Pop-Location
}

# 5. Launch Face Recognition Service (Port 5000)
Write-Host "`nLaunching Face Recognition Service (Port 5000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='Face Recognition Service (:5000)'; cd '$ScriptDir\Face_rec'; Write-Host 'Starting Face Recognition Service on port 5000...' -ForegroundColor Cyan; & '$pythonExe' app.py"

Start-Sleep -Seconds 2

# 6. Launch MQTT Worker
Write-Host "Launching MQTT Worker (Subscribes to door/face/pin topics)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='MQTT Worker'; cd '$ScriptDir\Backend'; `$env:MONGO_URI='mongodb://localhost:$mongoPort'; Write-Host 'Starting MQTT Worker...' -ForegroundColor Magenta; & '$pythonExe' mqtt_worker.py"

Start-Sleep -Seconds 2

# 7. Launch Backend HTTP Gateway (Port 3000)
Write-Host "Launching Backend HTTP Gateway (Port 3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='Backend HTTP Gateway (:3000)'; cd '$ScriptDir\Backend'; Write-Host 'Starting Backend Gateway on port 3000...' -ForegroundColor Green; & '$pythonExe' app.py"

Start-Sleep -Seconds 2

# 8. Launch Frontend Server (Port 8000)
Write-Host "Launching Frontend Server (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='Frontend Server (:8000)'; cd '$ScriptDir'; Write-Host 'Serving Frontend on http://localhost:8000...' -ForegroundColor Yellow; & '$pythonExe' -m http.server 8000 --directory Frontend"

Start-Sleep -Seconds 1

Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "  All 4 MQTT services launched successfully!" -ForegroundColor Green
Write-Host "  Opening http://localhost:8000 in your browser..." -ForegroundColor Green
Write-Host "  - Demo Door: Door1" -ForegroundColor White
Write-Host "  - Demo User: manish" -ForegroundColor White
Write-Host "  - Demo PIN:  1234" -ForegroundColor White
Write-Host "  - Face img:  Backend\faces\bob1.jpeg" -ForegroundColor White
Write-Host "======================================================" -ForegroundColor Green

Start-Process "http://localhost:8000"
