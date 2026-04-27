#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${CV_SW_TOOLCHAIN:-$PWD/tools/riscv-toolchain}"
PREFIX="${CV_SW_PREFIX:-riscv64-unknown-elf-}"

if command -v "${PREFIX}gcc" >/dev/null 2>&1; then
  echo "RISC-V toolchain already available: $(command -v "${PREFIX}gcc")"
  exit 0
fi

if [ -x "$INSTALL_DIR/bin/${PREFIX}gcc" ]; then
  echo "Using cached RISC-V toolchain at $INSTALL_DIR"
  exit 0
fi

if [ -n "${RISCV_TOOLCHAIN_TARBALL_URL:-}" ]; then
  mkdir -p "$INSTALL_DIR"
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT
  curl -L "$RISCV_TOOLCHAIN_TARBALL_URL" -o "$tmpdir/toolchain.tar.gz"
  tar -xzf "$tmpdir/toolchain.tar.gz" -C "$INSTALL_DIR" --strip-components="${RISCV_TOOLCHAIN_STRIP_COMPONENTS:-1}"
  "$INSTALL_DIR/bin/${PREFIX}gcc" --version
  exit 0
fi

sudo apt-get update
sudo apt-get install -y --no-install-recommends gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf
"${PREFIX}gcc" --version
