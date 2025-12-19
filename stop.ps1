# MistralTune - Stop All Services Script (Windows PowerShell)
# Stops all backend and frontend processes

$ErrorActionPreference = "Continue"

# Colors for output
function Write-ColorOutput {
    param($ForegroundColor)
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "=== MistralTune - Stopping All Services ==="
Write-Output ""

# Configuration
$BACKEND_PORT = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
$FRONTEND_PORT = if ($env:FRONTEND_PORT) { [int]$env:FRONTEND_PORT } else { 3000 }

$stoppedCount = 0

# Function to kill processes on a specific port
function Stop-ProcessOnPort {
    param([int]$Port)
    
    $pids = @()
    $connections = netstat -ano | Select-String ":$Port.*LISTENING"
    
    foreach ($conn in $connections) {
        if ($conn -match '\s+(\d+)\s*$') {
            $processId = [int]$matches[1]
            if ($processId -gt 0) {
                $pids += $processId
            }
        }
    }
    
    foreach ($processId in $pids) {
        try {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-ColorOutput Yellow "Stopping process on port $Port (PID: $processId) - $($process.ProcessName)"
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
                $script:stoppedCount++
            }
        } catch {
            # Process might already be gone
        }
    }
}

# Stop processes on backend port
Write-ColorOutput Cyan "Checking port $BACKEND_PORT (backend)..."
Stop-ProcessOnPort -Port $BACKEND_PORT

# Stop processes on frontend port
Write-ColorOutput Cyan "Checking port $FRONTEND_PORT (frontend)..."
Stop-ProcessOnPort -Port $FRONTEND_PORT

# Also check for processes by command line
Write-ColorOutput Cyan "Checking for processes by command line..."

$processes = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -like "*python*" -or $_.Name -eq "node.exe") -and
    $_.CommandLine -and
    ($_.CommandLine -match "mistraltune|uvicorn|fastapi|src\\api\\main\.py|frontend|next.*dev" -or
     $_.ExecutablePath -match "mistraltune")
}

foreach ($proc in $processes) {
    try {
        $process = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
        if ($process) {
            Write-ColorOutput Yellow "Stopping process (PID: $($proc.ProcessId)) - $($proc.CommandLine)"
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            $script:stoppedCount++
        }
    } catch {
        # Process might already be gone
    }
}

# Wait a moment for processes to fully terminate
Start-Sleep -Seconds 2

# Verify ports are free
Write-Output ""
Write-ColorOutput Cyan "Verifying ports are free..."

function Test-PortFree {
    param([int]$Port)
    $listening = netstat -ano | Select-String ":$Port.*LISTENING"
    if (-not $listening) {
        return $true
    }
    
    # Check if any listening process actually exists
    foreach ($line in $listening) {
        if ($line -match '\s+(\d+)\s*$') {
            $processId = [int]$matches[1]
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                return $false
            }
        }
    }
    
    # Only zombie connections remain
    return $null
}

$backendStatus = Test-PortFree -Port $BACKEND_PORT
if ($backendStatus -eq $true) {
    Write-ColorOutput Green "[OK] Port $BACKEND_PORT is free"
    $backendFree = $true
} elseif ($backendStatus -eq $null) {
    Write-ColorOutput Yellow "Warning: Port $BACKEND_PORT has zombie connections (will clear automatically)"
    Write-ColorOutput Yellow "  These are leftover connections that Windows will clean up in 30-60 seconds"
    $backendFree = $true  # Consider it free since no real process is using it
} else {
    Write-ColorOutput Red "Warning: Port $BACKEND_PORT is still in use by a real process"
    $backendFree = $false
}

$frontendStatus = Test-PortFree -Port $FRONTEND_PORT
if ($frontendStatus -eq $true) {
    Write-ColorOutput Green "[OK] Port $FRONTEND_PORT is free"
    $frontendFree = $true
} elseif ($frontendStatus -eq $null) {
    Write-ColorOutput Yellow "Warning: Port $FRONTEND_PORT has zombie connections (will clear automatically)"
    Write-ColorOutput Yellow "  These are leftover connections that Windows will clean up in 30-60 seconds"
    $frontendFree = $true  # Consider it free since no real process is using it
} else {
    Write-ColorOutput Red "Warning: Port $FRONTEND_PORT is still in use by a real process"
    $frontendFree = $false
}

Write-Output ""
if ($stoppedCount -gt 0) {
    Write-ColorOutput Green "Stopped $stoppedCount process(es)"
} else {
    Write-ColorOutput Yellow "No processes were found running"
}

if ($backendFree -and $frontendFree) {
    Write-ColorOutput Green "=== All services stopped successfully ==="
    exit 0
} else {
    Write-ColorOutput Yellow "=== Some ports may still be in use ==="
    Write-ColorOutput Yellow "You may need to wait a few seconds or manually check the ports"
    exit 1
}

