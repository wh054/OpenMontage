$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = '1'
$env:PATH = "$PSScriptRoot\.venv\Scripts;$PSScriptRoot\.runtime\ffmpeg\bin;" + $env:PATH
$env:HYPERFRAMES_BROWSER_PATH = "$PSScriptRoot\remotion-composer\node_modules\.remotion\chrome-headless-shell\win64\chrome-headless-shell-win64\chrome-headless-shell.exe"
$env:HYPERFRAMES_FFMPEG_PATH = "$PSScriptRoot\.runtime\ffmpeg\bin\ffmpeg.exe"
$env:HYPERFRAMES_FFPROBE_PATH = "$PSScriptRoot\.runtime\ffmpeg\bin\ffprobe.exe"
