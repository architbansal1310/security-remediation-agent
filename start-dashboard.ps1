$ErrorActionPreference = "Stop"
$agentRoot = $PSScriptRoot
Set-Location -LiteralPath $agentRoot
Write-Host "Opening Remedy dashboard at http://127.0.0.1:8080"
Start-Process "http://127.0.0.1:8080"
& (Join-Path $agentRoot "run.ps1") serve
