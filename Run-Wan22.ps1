param(
    [string]$Project = 'wan22-amd-14b-staged',
    [string]$Workflow = 'workflows/wan22-14b-480p-5s-staged-api.json',
    [string]$ServerLog = '.runtime/wan22/staged-server.stderr.log'
)
. "$PSScriptRoot\Enter-OpenMontage.ps1"
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
& "$PSScriptRoot\.venv\Scripts\python.exe" -u scripts\run_wan22.py --project $Project --workflow $Workflow --server-log $ServerLog
if ($LASTEXITCODE -ne 0) { throw 'Wan 2.2 benchmark failed. Inspect the project result and server logs before retrying.' }
