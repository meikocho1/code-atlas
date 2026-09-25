#!/usr/bin/env bash
# Build one evaluation scenario (default: state) as a demo repository; scenarios live in eval/scenarios/.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: bash scripts/make-fixture.sh NEW_DIRECTORY [SCENARIO]" >&2
  exit 2
fi
exec python3 "$(dirname "$0")/../eval/harness.py" build "${2:-state}" "$1"
