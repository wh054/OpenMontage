param([string]$Proxy = 'http://127.0.0.1:7890')
. "$PSScriptRoot\Enter-OpenMontage.ps1"
& "$PSScriptRoot\.venv\Scripts\python.exe" -u scripts\download_wan22.py --proxy $Proxy
if ($LASTEXITCODE -ne 0) { throw 'Wan 2.2 download or integrity verification failed.' }
