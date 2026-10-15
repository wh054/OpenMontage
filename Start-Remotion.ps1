param([int]$Port = 4751)
. "$PSScriptRoot\Enter-OpenMontage.ps1"
Set-Location "$PSScriptRoot\remotion-composer"
& npx.cmd --no-install remotion studio src/index.tsx --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Remotion Studio failed.' }
