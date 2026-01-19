#!/usr/bin/env bash
set -e

# Ensure hyperfine is available
if ! command -v hyperfine >/dev/null 2>&1; then
  echo "hyperfine not found, installing for current session..."
  cargo install hyperfine
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Run marimo notebook
uv run marimo run notebook_hyper.py
