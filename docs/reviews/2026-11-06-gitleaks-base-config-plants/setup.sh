#!/usr/bin/env bash
set -euo pipefail
if [[ ! -e node_modules ]]; then
  ln -s "${GITLEAKS_TEST_NODE_MODULES:?}" node_modules
fi
[[ "$(readlink node_modules)" == "${GITLEAKS_TEST_NODE_MODULES:?}" ]]
