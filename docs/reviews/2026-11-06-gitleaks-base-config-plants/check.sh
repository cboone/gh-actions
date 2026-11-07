#!/usr/bin/env bash
set -euo pipefail
printf "gitleaks plant: fixture started\n"
node tests/fixtures/gitleaks-plant-verdict.mjs
uv run --no-project --no-python-downloads --script tests/fixtures/gitleaks-errors-verdict.py
printf "GITLEAKS_VERDICT green\n"
