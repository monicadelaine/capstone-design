#!/bin/sh
# Run the automated test baseline: backend (pytest) and frontend (vitest).
#
# Usage:  scripts/test.sh            run both suites
#         scripts/test.sh backend    backend only
#         scripts/test.sh frontend   frontend only
#
# Requires the dev stack to be running:
#   docker compose -f docker-compose.dev.yml up -d
# Windows PowerShell users: .\scripts\test.ps1

set -u
cd "$(dirname "$0")/.." || exit 1

suite="${1:-all}"
case "$suite" in
  all|backend|frontend) ;;
  *) echo "usage: scripts/test.sh [backend|frontend]" >&2; exit 2 ;;
esac

compose="docker compose -f docker-compose.dev.yml"
failed=0

if [ "$suite" = "all" ] || [ "$suite" = "backend" ]; then
  echo "==> Backend tests (pytest)"
  $compose exec -T backend pytest -q || failed=1
fi

if [ "$suite" = "all" ] || [ "$suite" = "frontend" ]; then
  echo "==> Frontend tests (vitest)"
  $compose exec -T frontend npm run test || failed=1
fi

if [ "$failed" -ne 0 ]; then
  echo "==> FAILED: at least one suite did not pass" >&2
  exit 1
fi
echo "==> All suites passed"
