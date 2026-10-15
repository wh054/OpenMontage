param(
    [ValidateSet('wan21', 'wan22')][string]$Version = 'wan22',
    [string]$ComfyRoot = $env:OPENMONTAGE_COMFY_ROOT,
    [string]$ComfyPython = $env:OPENMONTAGE_COMFY_PYTHON
)
$ErrorActionPreference = 'Stop'
if (-not $ComfyRoot) { $ComfyRoot = 'E:\Qwen-Image-2.1\ComfyUI' }
if (-not $ComfyPython) { $ComfyPython = Join-Path (Split-Path $ComfyRoot -Parent) '.venv\Scripts\python.exe' }
$wanComfyMain = Join-Path $ComfyRoot 'main.py'
foreach ($wanRequiredPath in @($wanComfyMain, $ComfyPython)) {
    if (-not (Test-Path -LiteralPath $wanRequiredPath -PathType Leaf)) {
        throw "Missing $wanRequiredPath. Set -ComfyRoot/-ComfyPython or OPENMONTAGE_COMFY_ROOT/OPENMONTAGE_COMFY_PYTHON to your existing ROCm environment."
    }
}
$wanComfyPython = (Resolve-Path -LiteralPath $ComfyPython).Path
$wanComfyMain = (Resolve-Path -LiteralPath $wanComfyMain).Path
$wanRuntimeDir = Join-Path $PSScriptRoot ".runtime\$Version"
[void][System.IO.Directory]::CreateDirectory($wanRuntimeDir)
$wanModelConfig = Join-Path $wanRuntimeDir 'model_paths.yaml'
# JSON-quoted strings are also valid YAML; this handles spaces and backslashes.
$wanSharedModels = (Join-Path $PSScriptRoot '.runtime\wan21\models') | ConvertTo-Json -Compress
$wanConfigText = @"
openmontage_wan21_shared:
  base_path: $wanSharedModels
  diffusion_models: diffusion_models
  text_encoders: text_encoders
  vae: vae
"@
if ($Version -eq 'wan22') {
    $wanVideoModels = (Join-Path $PSScriptRoot '.runtime\wan22\models') | ConvertTo-Json -Compress
    $wanRepoPath = $PSScriptRoot | ConvertTo-Json -Compress
    $wanConfigText += @"

openmontage_wan22:
  base_path: $wanVideoModels
  diffusion_models: diffusion_models
  loras: loras
openmontage_runtime:
  base_path: $wanRepoPath
  custom_nodes: comfy_nodes
"@
}
if (Test-Path -LiteralPath $wanModelConfig) {
    $wanOldConfig = [System.IO.File]::ReadAllText($wanModelConfig)
    if ($wanOldConfig.Trim() -ne $wanConfigText.Trim()) {
        Copy-Item -LiteralPath $wanModelConfig -Destination ($wanModelConfig + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    }
}
[System.IO.File]::WriteAllText($wanModelConfig, $wanConfigText + "`n", [System.Text.UTF8Encoding]::new($false))
