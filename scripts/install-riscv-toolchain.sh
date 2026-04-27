#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${CV_SW_TOOLCHAIN:-$PWD/tools/riscv-toolchain}"
PREFIX="${CV_SW_PREFIX:-riscv64-unknown-elf-}"

has_complete_toolchain() {
  local extra_cflags=()
  local picolibc_specs
  picolibc_specs="$("${PREFIX}gcc" --print-file-name=picolibc.specs 2>/dev/null || true)"
  if [ -n "$picolibc_specs" ] && [ "$picolibc_specs" != "picolibc.specs" ]; then
    extra_cflags+=(--specs=picolibc.specs)
  fi

  command -v "${PREFIX}gcc" >/dev/null 2>&1 &&
    printf '#include <sys/stat.h>\nint main(void) { return 0; }\n' |
      "${PREFIX}gcc" "${extra_cflags[@]}" -x c - -c -o /tmp/cv32e20-riscv-toolchain-check.o >/dev/null 2>&1
}

if has_complete_toolchain; then
  echo "RISC-V toolchain already available: $(command -v "${PREFIX}gcc")"
  exit 0
fi

if [ -x "$INSTALL_DIR/bin/${PREFIX}gcc" ] && has_complete_toolchain; then
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
sudo apt-get install -y --no-install-recommends \
  gcc-riscv64-unknown-elf \
  binutils-riscv64-unknown-elf \
  picolibc-riscv64-unknown-elf
"${PREFIX}gcc" --version
has_complete_toolchain
