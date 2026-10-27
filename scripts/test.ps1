# Run the automated test baseline: backend (pytest) and frontend (vitest).
#
# Usage:  .\scripts\test.ps1              run both suites
#         .\scripts\test.ps1 backend      backend only
#         .\scripts\test.ps1 frontend     frontend only
#
# Requires the dev stack to be running:
#   docker compose -f docker-compose.dev.yml up -d
# macOS, Linux, and Git Bash users: scripts/test.sh

param(
    [ValidateSet('all', 'backend', 'frontend')]
    [string]$Suite = 'all'
)

Set-Location (Join-Path $PSScriptRoot '..')
$compose = @('compose', '-f', 'docker-compose.dev.yml')
$failed = $false

if ($Suite -in 'all', 'backend') {
    Write-Host '==> Backend tests (pytest)'
    & docker @compose exec -T backend pytest -q
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if ($Suite -in 'all', 'frontend') {
    Write-Host '==> Frontend tests (vitest)'
    & docker @compose exec -T frontend npm run test
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}

if ($failed) {
    Write-Host '==> FAILED: at least one suite did not pass'
    exit 1
}
Write-Host '==> All suites passed'
exit 0
