#!/usr/bin/env bash
set -euo pipefail
if [[ ! -e node_modules ]]; then
  ln -s "${UV_PIN_NODE_MODULES:?}" node_modules
fi
node --check tests/fixtures/workflow-steps.mjs
node --check tests/fixtures/check-workflow-arg-binding.mjs
