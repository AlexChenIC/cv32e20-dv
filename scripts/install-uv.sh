#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv --version
  exit 0
fi

curl -LsSf https://astral.sh/uv/install.sh | sh
echo "$HOME/.local/bin" >> "$GITHUB_PATH"
"$HOME/.local/bin/uv" --version
