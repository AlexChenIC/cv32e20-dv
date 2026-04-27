#!/usr/bin/env bash
set -euo pipefail

simulator="${1:-${SIMULATOR:-vsim}}"

cd "${CV32E20_DV_ROOT:-$PWD}/sim/uvmt"
make test COREV=YES TEST=hello-world SIMULATOR="$simulator"
