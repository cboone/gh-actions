#!/usr/bin/env bash
# check.sh -- Check that local targets propagate a failed tool invocation.
set -euo pipefail
printf "Checking Makefile failure propagation\n"
for target in test-setup-uv test-scrut-installation test-zig-format-paths \
  test-workflow-arg-binding test-npm-publish test-trufflehog-positive-control \
  test-scrut-release-audit test-shell-discovery test-tool-version-reporting \
  test-gitleaks-config-errors test-rust-tool-installs test-checkout-credentials \
  test-gitleaks-base-config audit-scrut-releases test-scrut test-python test-node test test-network; do
  code=0
  make "${target}" NODE=/usr/bin/false UV=/usr/bin/false SCRUT=/usr/bin/false >target.log 2>&1 || code=$?
  if [[ "${code}" != 2 ]] || ! grep -Fq "/usr/bin/false" target.log || ! grep -Fq "Error 1" target.log; then
    printf "FAIL: %s accepted a failing tool (make exit %s)\n" "${target}" "${code}"
    exit 1
  fi
done
printf "PASS: every target propagated a failed tool\n"
