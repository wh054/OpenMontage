param(
    [int]$Port = 8188,
    [string]$ComfyRoot = $env:OPENMONTAGE_COMFY_ROOT,
    [string]$ComfyPython = $env:OPENMONTAGE_COMFY_PYTHON,
    [string]$Proxy = 'http://127.0.0.1:7890'
)
. "$PSScriptRoot\Enter-OpenMontage.ps1"
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    throw "Port $Port is already occupied. Inspect the existing service before starting another."
}
. "$PSScriptRoot\Initialize-WanRuntime.ps1" -Version wan21 -ComfyRoot $ComfyRoot -ComfyPython $ComfyPython
$env:HTTP_PROXY = $Proxy
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:COMFYUI_VIDEO_SERVER_URL = "http://127.0.0.1:$Port"
& $wanComfyPython -s $wanComfyMain --listen 127.0.0.1 --port $Port --disable-api-nodes --reserve-vram 1.5 --use-pytorch-cross-attention --disable-pinned-memory --extra-model-paths-config $wanModelConfig
if ($LASTEXITCODE -ne 0) { throw 'ComfyUI failed. See server log.' }
