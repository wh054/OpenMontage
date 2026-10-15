param([int]$Port = 4750)
. "$PSScriptRoot\Enter-OpenMontage.ps1"
$env:BACKLOT_PORT = "$Port"
& "$PSScriptRoot\.venv\Scripts\python.exe" -m backlot open
if ($LASTEXITCODE -ne 0) { throw 'Backlot could not start.' }
