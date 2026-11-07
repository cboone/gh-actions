#!/usr/bin/env bash
set -euo pipefail
readonly FIXTURE_DIR="docs/reviews/2026-11-06-uv-pin-agreement-plants"
[[ -f "${FIXTURE_DIR}/semgrep-error.json" ]]
jq -e '(.results | type == "array") and (.errors | type == "array") and all(.errors[]; type == "object")' "${FIXTURE_DIR}/semgrep-error.json" >/dev/null
printf 'semgrep acceptance reached\n'
if jq -e -f "${FIXTURE_DIR}/semgrep-accept.jq" "${FIXTURE_DIR}/semgrep-error.json" >/dev/null; then
  printf 'semgrep verdict: accepted\n'
else
  check_exit=$?
  [[ "${check_exit}" -eq 1 ]] || exit 2
  printf 'semgrep verdict: rejected\n'
  exit 1
fi
