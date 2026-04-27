#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${SAIL_RISCV_INSTALL_DIR:-$PWD/tools/sail-riscv}"

if command -v sail_riscv_sim >/dev/null 2>&1; then
  echo "Sail RISC-V already available: $(command -v sail_riscv_sim)"
  exit 0
fi

if [ -x "$INSTALL_DIR/bin/sail_riscv_sim" ]; then
  echo "Using cached Sail RISC-V at $INSTALL_DIR"
  exit 0
fi

if [ -z "${SAIL_RISCV_TARBALL_URL:-}" ]; then
  echo "SAIL_RISCV_TARBALL_URL is not set and sail_riscv_sim is not on PATH" >&2
  echo "Set SAIL_RISCV_TARBALL_URL to a Sail RISC-V v0.10 binary tarball or preinstall sail_riscv_sim." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
curl -L "$SAIL_RISCV_TARBALL_URL" -o "$tmpdir/sail-riscv.tar.gz"
tar -xzf "$tmpdir/sail-riscv.tar.gz" -C "$INSTALL_DIR" --strip-components="${SAIL_RISCV_STRIP_COMPONENTS:-1}"
"$INSTALL_DIR/bin/sail_riscv_sim" --help >/dev/null
