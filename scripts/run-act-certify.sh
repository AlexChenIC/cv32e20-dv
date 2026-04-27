#!/usr/bin/env bash
set -euo pipefail

cd "${CV32E20_DV_ROOT:-$PWD}/sim/core"
make gen-certify

summary="simulation_results/certification/test_program/bsp/certification_summary.txt"
if [ -f "$summary" ]; then
  cat "$summary"
else
  echo "Missing ACT4 summary: $summary" >&2
  exit 1
fi
