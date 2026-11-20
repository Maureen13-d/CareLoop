# Run the backend suite and the frontend type check.
# Tests use an in-memory database and do not read or write backend/careloop.db.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Missing $python. Create the backend virtualenv first."
}
Push-Location (Join-Path $root "backend")
& $python -m pytest -q --tb=line
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
Pop-Location
Push-Location (Join-Path $root "frontend")
npx tsc --noEmit
$code = $LASTEXITCODE
Pop-Location
exit $code
