#!/usr/bin/env bash
set -euo pipefail

if command -v udb >/dev/null 2>&1; then
  udb --version || true
  exit 0
fi

if [ "${REQUIRE_UDB:-false}" = "true" ]; then
  echo "UDB is required for this job but was not found on PATH." >&2
  exit 1
fi

echo "UDB not found; continuing because REQUIRE_UDB is not true."
