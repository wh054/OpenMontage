param([string]$Project = 'wan21-amd-validation', [string]$ResumePromptId = '', [string]$Workflow = '')
. "$PSScriptRoot\Enter-OpenMontage.ps1"
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
$params = @('-u','scripts\run_wan21.py','--project',$Project)
if ($Workflow) { $params += @('--workflow',$Workflow) }
if ($ResumePromptId) { $params += @('--resume-prompt-id',$ResumePromptId) }
& "$PSScriptRoot\.venv\Scripts\python.exe" @params
if ($LASTEXITCODE -ne 0) { throw 'Generation failed. Inspect the project generation-result.json and ComfyUI logs before retrying.' }
