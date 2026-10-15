param([int]$Port = 8188)
$ErrorActionPreference = 'Stop'
$listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $listener) { Write-Output 'Wan 2.2 service is not listening.'; return }
$ownerId = $listener[0].OwningProcess
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId"
$configPath = Join-Path $PSScriptRoot '.runtime\wan22\model_paths.yaml'
if ($process.CommandLine -notlike '*main.py*' -or $process.CommandLine -notlike "*$configPath*") {
    throw 'Port owner does not match the Wan 2.2 configuration; it was not stopped.'
}
Stop-Process -Id $ownerId
Wait-Process -Id $ownerId -Timeout 10 -ErrorAction SilentlyContinue
$releaseDeadline = (Get-Date).AddSeconds(10)
while (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    if ((Get-Date) -gt $releaseDeadline) { throw "Port $Port was not released after stopping the video service." }
    Start-Sleep -Milliseconds 250
}
Write-Output "Stopped Wan 2.2 ComfyUI on port $Port."
