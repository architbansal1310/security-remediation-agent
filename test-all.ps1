$ErrorActionPreference = "Stop"
$agentRoot = $PSScriptRoot
$targetRoot = Join-Path (Split-Path $agentRoot -Parent) "vulnerable-java-platform"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonCandidates = @()
if ($pythonCommand) { $pythonCandidates += $pythonCommand.Source }
$pythonCandidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$pythonExecutable = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $pythonExecutable) { throw "Python 3.11+ was not found." }

Write-Host "[1/5] Running Python remediation-worker tests..." -ForegroundColor Cyan
& $pythonExecutable -m unittest discover -s (Join-Path $agentRoot "tests") -v
if ($LASTEXITCODE -ne 0) { throw "Agent tests failed." }

Write-Host "[2/5] Building the REST service and enforcing 70%+ coverage..." -ForegroundColor Cyan
Push-Location -LiteralPath $agentRoot
try {
  & (Join-Path $agentRoot "mvnw.cmd") --batch-mode --no-transfer-progress verify
  if ($LASTEXITCODE -ne 0) { throw "REST service validation failed." }
} finally {
  Pop-Location
}

Write-Host "[3/5] Building and testing both target Java APIs..." -ForegroundColor Cyan
Push-Location -LiteralPath $targetRoot
try {
  & (Join-Path $targetRoot "mvnw.cmd") --batch-mode --no-transfer-progress verify
  if ($LASTEXITCODE -ne 0) { throw "Java validation failed." }
} finally {
  Pop-Location
}

Write-Host "[4/5] Analyzing the parent-managed Critical finding..." -ForegroundColor Cyan
& (Join-Path $agentRoot "run.ps1") analyze --report (Join-Path $agentRoot "samples\nexus-parent-report.json") --repo $targetRoot
if ($LASTEXITCODE -ne 0) { throw "Parent analysis failed." }

Write-Host "[5/5] Analyzing the child-owned High finding..." -ForegroundColor Cyan
& (Join-Path $agentRoot "run.ps1") analyze --report (Join-Path $agentRoot "samples\prisma-child-report.json") --repo $targetRoot
if ($LASTEXITCODE -ne 0) { throw "Child analysis failed." }

Write-Host "All tests and analyses passed." -ForegroundColor Green
