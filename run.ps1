param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]] $RemediatorArguments
)

$ErrorActionPreference = "Stop"
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$candidates = @()
if ($pythonCommand) { $candidates += $pythonCommand.Source }
$candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

$pythonExecutable = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $pythonExecutable) {
  throw "Python 3.11+ was not found. Install Python from python.org, then run this command again."
}

& $pythonExecutable (Join-Path $PSScriptRoot "remediator.py") @RemediatorArguments
exit $LASTEXITCODE
