#!/usr/bin/env bash
set -euo pipefail

cd "${CV32E20_DV_ROOT:-$PWD}/sim/core"
make sanity

summary="simulation_results/hello-world/0/test_program/bsp/hello-world.log"
if [ -f "$summary" ]; then
  tail -80 "$summary"
fi
