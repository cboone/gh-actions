#!/usr/bin/env bash
# Build Scrut's pinned source with the reviewed dependency lockfile.
set -euo pipefail

function main() {
  local source_rev="04ecce97e63c354e0374961ac977cc678d0f3932"
  local source_checksum="947997a4a7140ee57183eb0cc448774e074e0bc5477c942190da4ac4fd4555cd"
  local source_dir archive actual install_dir script_dir host_target
  if [[ "${VERSION}" != "0.4.3" ]]; then
    echo "Unsupported scrut version: ${VERSION}; source pins support only 0.4.3." >&2
    exit 1
  fi
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  source_dir="$(mktemp -d "${RUNNER_TEMP}/scrut-source.XXXXXX")"
  archive="${source_dir}/source.tar.gz"
  curl -sSfL -o "${archive}" "https://github.com/facebookincubator/scrut/archive/${source_rev}.tar.gz"
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "${archive}" | awk '{print $1}')"
  else
    actual="$(shasum -a 256 "${archive}" | awk '{print $1}')"
  fi
  if [[ "${actual}" != "${source_checksum}" ]]; then
    echo "Scrut source archive checksum verification failed." >&2
    exit 1
  fi
  tar -xzf "${archive}" -C "${source_dir}" --strip-components=1
  cp "${script_dir}/Cargo.lock" "${source_dir}/Cargo.lock"
  # --locked rejects dependency resolution changes and verifies crate checksums.
  # Select the pinned compiler even if a caller has a toolchain override.
  host_target="$(rustc +1.97.1 -vV | sed -n 's/^host: //p')"
  (
    cd "${source_dir}"
    CARGO_TARGET_DIR="${source_dir}/target" cargo +1.97.1 build --release --locked --target "${host_target}" --bin scrut
  )
  install_dir="${RUNNER_TEMP}/scrut-bin"
  mkdir -p "${install_dir}"
  cp "${source_dir}/target/${host_target}/release/scrut" "${install_dir}/scrut"
  "${install_dir}/scrut" --version
  printf '%s\n' "${install_dir}" >>"${GITHUB_PATH}"
}

main "$@"
