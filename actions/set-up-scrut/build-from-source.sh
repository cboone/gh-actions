#!/usr/bin/env bash
# Build Scrut's pinned source with the reviewed dependency lockfile.
set -euo pipefail

function main() {
  local source_rev="04ecce97e63c354e0374961ac977cc678d0f3932"
  local source_checksum="947997a4a7140ee57183eb0cc448774e074e0bc5477c942190da4ac4fd4555cd"
  local source_dir archive actual install_dir script_dir host_target ancestor config name version_output
  if [[ "${VERSION}" != "0.4.3" ]]; then
    echo "Unsupported scrut version: ${VERSION}; source pins support only 0.4.3." >&2
    exit 1
  fi
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  source_dir="$(mktemp -d /tmp/scrut-source.XXXXXX)"
  source_dir="$(cd "${source_dir}" && pwd -P)"
  readonly SCRUT_SOURCE_DIR="${source_dir}"
  trap 'rm -r "${SCRUT_SOURCE_DIR}"' EXIT
  archive="${source_dir}/source.tar.gz"
  curl -sSfL --proto '=https' --proto-redir '=https' -o "${archive}" "https://github.com/facebookincubator/scrut/archive/${source_rev}.tar.gz"
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
  # Cargo walks the working directory's ancestors as well as CARGO_HOME.
  ancestor="${source_dir}"
  while :; do
    for config in "${ancestor}/.cargo/config.toml" "${ancestor}/.cargo/config"; do
      if [[ -e "${config}" ]]; then
        echo "::error::A Cargo config at ${config} would change the Scrut source build." >&2
        exit 1
      fi
    done
    [[ "${ancestor}" == "/" ]] && break
    ancestor="$(dirname "${ancestor}")"
  done
  export CARGO_HOME="${source_dir}/cargo-home"
  mkdir -p "${CARGO_HOME}"
  unset RUSTFLAGS CARGO_ENCODED_RUSTFLAGS RUSTC RUSTC_WRAPPER RUSTC_WORKSPACE_WRAPPER
  while IFS='=' read -r name _; do
    case "${name}" in
      CARGO_BUILD_* | CARGO_TARGET_* | CARGO_PROFILE_*) unset "${name}" ;;
    esac
  done < <(env)
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
  # Upstream build.rs falls back to a timestamp when archive builds lack Git
  # metadata. Verify and report this documented limitation rather than treating
  # the timestamp as proof of the release pin; source bytes establish that pin.
  version_output="$("${install_dir}/scrut" --version)"
  if [[ ! "${version_output}" =~ ^scrut\ [0-9]+$ ]]; then
    echo "::error::Unexpected Scrut archive-build version: ${version_output}" >&2
    exit 1
  fi
  printf '%s\n' "${version_output}"
  printf '%s\n' "${install_dir}" >>"${GITHUB_PATH}"
}

(main "$@")
