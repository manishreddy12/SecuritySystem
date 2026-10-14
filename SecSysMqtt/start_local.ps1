# =========================================================
# SecSysMqtt — Local Launcher (MQTT Event-Driven Edition)
# =========================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  Starting SecSysMqtt (MQTT Security System)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 0. Detect Python executable
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

# 1. Clean up stale processes
Write-Host "Cleaning up previous processes on ports 3000, 5000, 8000..." -ForegroundColor Gray
foreach ($port in @(3000, 5000, 8000)) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

# 2. Check Mosquitto broker (port 1883)
Write-Host "`nChecking Mosquitto MQTT Broker (port 1883)..." -ForegroundColor Cyan
$mqttOk = $false
try {
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 1883 -WarningAction SilentlyContinue
    if ($conn.TcpTestSucceeded) { $mqttOk = $true }
} catch {}

if ($mqttOk) {
    Write-Host "[OK] Mosquitto is running on port 1883" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Mosquitto MQTT broker is NOT running on port 1883." -ForegroundColor Red
    Write-Host "        Install with: winget install EclipseFoundation.Mosquitto" -ForegroundColor Yellow
    Write-Host "        Then start:   Start-Service mosquitto" -ForegroundColor Yellow
    exit 1
}

# 3. Detect MongoDB port
$mongoPort = 27017
$mongoOk = $false
foreach ($port in @(27017, 23017)) {
    try {
        $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -WarningAction SilentlyContinue
        if ($conn.TcpTestSucceeded) {
            $mongoOk = $true
            $mongoPort = $port
            break
        }
    } catch {}
}

if ($mongoOk) {
    Write-Host "[OK] MongoDB is running on port $mongoPort" -ForegroundColor Green
    $env:MONGO_URI = "mongodb://localhost:$mongoPort"
} else {
    Write-Host "[ERROR] MongoDB is not running on port 27017 or 23017." -ForegroundColor Red
    Write-Host "        Start MongoDB first: Get-Service MongoDB | Start-Service" -ForegroundColor Yellow
    exit 1
}

# 4. Seed Demo Data
Write-Host "`nSeeding demo data (Door1 / user manish / PIN 1234)..." -ForegroundColor Cyan
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
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='[SecSysMqtt] Face Recognition (:5000)'; cd '$ScriptDir\Face_rec'; Write-Host 'Starting Face Recognition Service...' -ForegroundColor Cyan; & '$pythonExe' app.py"

Start-Sleep -Seconds 2

# 6. Launch MQTT Worker (Port 1883)
Write-Host "Launching MQTT Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='[SecSysMqtt] MQTT Worker'; cd '$ScriptDir\Backend'; `$env:MONGO_URI='mongodb://localhost:$mongoPort'; Write-Host 'Starting MQTT Worker...' -ForegroundColor Magenta; & '$pythonExe' mqtt_worker.py"

Start-Sleep -Seconds 2

# 7. Launch Backend HTTP Gateway (Port 3000)
Write-Host "Launching Backend HTTP Gateway (Port 3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='[SecSysMqtt] Backend Gateway (:3000)'; cd '$ScriptDir\Backend'; `$env:MONGO_URI='mongodb://localhost:$mongoPort'; Write-Host 'Starting Backend Gateway...' -ForegroundColor Green; & '$pythonExe' app.py"

Start-Sleep -Seconds 2

# 8. Launch Frontend Server (Port 8000)
Write-Host "Launching Frontend Server (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$Host.UI.RawUI.WindowTitle='[SecSysMqtt] Frontend (:8000)'; cd '$ScriptDir'; Write-Host 'Serving Frontend on http://localhost:8000...' -ForegroundColor Yellow; & '$pythonExe' -m http.server 8000 --directory Frontend"

Start-Sleep -Seconds 1

Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "  All 4 services launched!" -ForegroundColor Green
Write-Host "  Opening http://localhost:8000 in your browser..." -ForegroundColor Green
Write-Host "  - Demo Door: Door1" -ForegroundColor White
Write-Host "  - Demo User: manish" -ForegroundColor White
Write-Host "  - Demo PIN:  1234" -ForegroundColor White
Write-Host "  - Face img:  Backend\faces\bob1.jpeg" -ForegroundColor White
Write-Host "======================================================" -ForegroundColor Green

Start-Process "http://localhost:8000"
