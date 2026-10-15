param([int]$Port = 8188)
$ErrorActionPreference = 'Stop'
$listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $listener) { Write-Output 'Wan ComfyUI is not running on this port.'; return }
$ownerId = $listener[0].OwningProcess
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId"
$configPath = Join-Path $PSScriptRoot '.runtime\wan21\model_paths.yaml'
if ($process.CommandLine -notlike '*main.py*' -or $process.CommandLine -notlike "*$configPath*") {
    throw "Port $Port belongs to a different service; it was not stopped."
}
Stop-Process -Id $ownerId
Write-Output "Stopped the Wan ComfyUI service on port $Port."
