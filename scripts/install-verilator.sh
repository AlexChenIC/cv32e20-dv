#!/usr/bin/env bash
set -euo pipefail

VERILATOR_VERSION="${VERILATOR_VERSION:-5.046}"
INSTALL_DIR="${VERILATOR_INSTALL_DIR:-$PWD/tools/verilator-$VERILATOR_VERSION}"

if command -v verilator >/dev/null 2>&1; then
  if verilator --version | grep -q "$VERILATOR_VERSION"; then
    echo "Verilator $VERILATOR_VERSION already available: $(command -v verilator)"
    exit 0
  fi
fi

if [ -x "$INSTALL_DIR/bin/verilator" ]; then
  echo "Using cached Verilator at $INSTALL_DIR"
  exit 0
fi

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  autoconf bison build-essential ca-certificates flex git help2man \
  libfl-dev libfl2 libgoogle-perftools-dev numactl perl python3 zlib1g-dev

mkdir -p "$(dirname "$INSTALL_DIR")"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

git clone --depth 1 --branch "v$VERILATOR_VERSION" https://github.com/verilator/verilator.git "$tmpdir/verilator"
cd "$tmpdir/verilator"
autoconf
./configure --prefix="$INSTALL_DIR"
make -j"$(nproc)"
make install

"$INSTALL_DIR/bin/verilator" --version
