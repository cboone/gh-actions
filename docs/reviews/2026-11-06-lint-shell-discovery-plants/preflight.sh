#!/usr/bin/env bash
set -euo pipefail
uv run --no-project python docs/reviews/2026-11-06-lint-shell-discovery-plants/check.py --preflight
