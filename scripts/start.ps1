$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}
& podman compose up -d --build
