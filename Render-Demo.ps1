param([ValidateSet('world-in-numbers','code-to-screen','focusflow-pitch')][string]$Demo = 'code-to-screen')
. "$PSScriptRoot\Enter-OpenMontage.ps1"
& "$PSScriptRoot\.venv\Scripts\python.exe" render_demo.py $Demo
if ($LASTEXITCODE -ne 0) { throw 'Demo render failed.' }
