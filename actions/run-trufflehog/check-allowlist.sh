#!/usr/bin/env bash
#
# Decide whether TruffleHog's findings are all covered by a reviewed
# allowlist, and report them with safe metadata only.
#
# Usage: check-allowlist.sh --findings <path> --allowlist <path>
#                          [--expect-findings]
#
# --expect-findings says TruffleHog exited 183, meaning it reported results.
# Seeing none in the file then means the two disagree, which is treated as a
# broken scan rather than a clean one.
#
# The findings file holds TruffleHog's --json output and therefore raw
# credential material. It is read here and never echoed: the report carries
# only the detector, verification state, commit, path and line. Its caller
# owns the file and removes it.
#
# Exit status:
#   0  every finding is allowlisted, or there were none
#   1  at least one finding is not allowlisted
#   2  the allowlist or the findings file could not be used

set -euo pipefail

readonly EXIT_BLOCKED=1
readonly EXIT_INVALID=2

function usage() {
  echo "Usage: ${0##*/} --findings <path> --allowlist <path> [--expect-findings]" >&2
}

function fail_invalid() {
  echo "::error::${1}" >&2
  exit "${EXIT_INVALID}"
}

function main() {
  local findings=""
  local allowlist=""
  local expect_findings="false"

  while [[ $# -gt 0 ]]; do
    case "${1}" in
    --findings)
      [[ $# -ge 2 ]] || {
        usage
        exit "${EXIT_INVALID}"
      }
      findings="${2}"
      shift 2
      ;;
    --allowlist)
      [[ $# -ge 2 ]] || {
        usage
        exit "${EXIT_INVALID}"
      }
      allowlist="${2}"
      shift 2
      ;;
    --expect-findings)
      expect_findings="true"
      shift
      ;;
    *)
      usage
      exit "${EXIT_INVALID}"
      ;;
    esac
  done

  if [[ -z "${findings}" || -z "${allowlist}" ]]; then
    usage
    exit "${EXIT_INVALID}"
  fi

  # jq comes from the runner image rather than an install step. Leaving a
  # tool to the image can fail open, so its absence is a hard failure here
  # instead of a skipped check that would pass every finding silently.
  if ! command -v jq >/dev/null 2>&1; then
    fail_invalid "jq is required to apply a TruffleHog allowlist and was not found on PATH."
  fi

  if [[ ! -f "${findings}" ]]; then
    fail_invalid "TruffleHog findings file not found: ${findings}"
  fi

  if [[ ! -f "${allowlist}" ]]; then
    fail_invalid "TruffleHog allowlist file not found: ${allowlist}"
  fi

  local program
  # CDPATH would otherwise resolve a relative directory somewhere else, and
  # -- keeps a leading dash in the path from reading as an option.
  program="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/check-allowlist.jq"

  if [[ ! -f "${program}" ]]; then
    fail_invalid "Allowlist matching program not found beside this script: ${program}"
  fi

  # Check the findings parse before the matching run, discarding the
  # diagnostic: a parse error can quote the input it choked on, and that
  # input is credential material. The allowlist's own errors are reported in
  # full below, because an allowlist holds no secrets.
  if ! jq . "${findings}" >/dev/null 2>&1; then
    fail_invalid "TruffleHog's findings were not valid JSON; the scan output cannot be matched."
  fi

  local report
  local status=0
  report="$(
    jq -r \
      --slurpfile allowlist "${allowlist}" \
      --slurpfile findings "${findings}" \
      -n -f "${program}"
  )" || status=$?

  if [[ "${status}" -ne 0 ]]; then
    fail_invalid "Could not match TruffleHog findings against ${allowlist}; see the jq error above."
  fi

  # The first line is the verdict, and nothing the allowlist controls can
  # precede it. Reading the count from there rather than grepping the report
  # keeps an entry's free text out of the decision.
  local summary="${report%%$'\n'*}"
  local body="${report#*$'\n'}"
  local blocked="${summary#status blocked=}"
  blocked="${blocked%% *}"
  local seen="${summary##*findings=}"

  if [[ "${summary}" != "status blocked="* ]] ||
    [[ ! "${blocked}" =~ ^[0-9]+$ ]] ||
    [[ ! "${seen}" =~ ^[0-9]+$ ]]; then
    fail_invalid "The allowlist report did not start with a verdict line."
  fi

  printf '%s\n' "${body}"

  # TruffleHog said it reported results, so the checker must have seen some.
  # Disagreement means the scan wrote something the checker cannot read, and
  # treating that as a clean run would pass a finding nobody reviewed.
  if [[ "${expect_findings}" == "true" && "${seen}" -eq 0 ]]; then
    fail_invalid "TruffleHog reported findings, but none reached the allowlist checker."
  fi

  if [[ "${blocked}" -gt 0 ]]; then
    echo "::error::TruffleHog reported findings that no allowlist entry covers." >&2
    exit "${EXIT_BLOCKED}"
  fi
}

main "$@"
