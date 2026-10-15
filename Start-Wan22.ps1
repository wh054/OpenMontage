param(
    [int]$Port = 8188,
    [string]$ComfyRoot = $env:OPENMONTAGE_COMFY_ROOT,
    [string]$ComfyPython = $env:OPENMONTAGE_COMFY_PYTHON,
    [string]$Proxy = 'http://127.0.0.1:7890'
)
. "$PSScriptRoot\Enter-OpenMontage.ps1"
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    throw "Port $Port is occupied. Stop the intended video service before starting this configuration."
}
. "$PSScriptRoot\Initialize-WanRuntime.ps1" -Version wan22 -ComfyRoot $ComfyRoot -ComfyPython $ComfyPython
$env:HTTP_PROXY = $Proxy
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
# NORMAL_VRAM is the default in this ComfyUI version. --lowvram forces CPU text encoding.
& $wanComfyPython -s $wanComfyMain --listen 127.0.0.1 --port $Port --disable-api-nodes --reserve-vram 1.5 --disable-smart-memory --cache-none --disable-pinned-memory --use-pytorch-cross-attention --extra-model-paths-config $wanModelConfig
if ($LASTEXITCODE -ne 0) { throw 'Wan 2.2 ComfyUI service failed.' }
