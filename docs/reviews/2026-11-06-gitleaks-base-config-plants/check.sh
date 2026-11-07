#!/usr/bin/env bash
set -euo pipefail
printf "gitleaks plant: fixture started\n"
node tests/check-gitleaks-base-config.mjs
uv run --no-project --no-python-downloads --script tests/check-gitleaks-config-errors.py
