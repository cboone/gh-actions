# Scrut Checksum Verification

## Context

Issue #6: All tool downloads in this repository verify SHA-256 checksums except scrut. The scrut project (facebookincubator/scrut) does not publish checksum files with its releases. PR #4 added checksum verification for every other tool but had to skip scrut for this reason.

Since upstream still does not publish checksums (confirmed: v0.4.3 release has no checksum assets), we will hardcode known-good SHA-256 hashes computed from the release tarballs. This is a standard approach when upstream lacks checksum files (similar to Homebrew formulae).

## Plan

### Step 1: Compute SHA-256 checksums for scrut v0.4.3 tarballs

Download all 4 platform tarballs and compute their SHA-256 hashes:

- `scrut-v0.4.3-linux-x86_64.tar.gz`
- `scrut-v0.4.3-linux-aarch64.tar.gz`
- `scrut-v0.4.3-macos-x86_64.tar.gz`
- `scrut-v0.4.3-macos-aarch64.tar.gz`

### Step 2: Update `actions/setup-scrut/action.yml`

After the existing `arch` case statement (line 33), add a new case statement mapping `${os}-${arch}` to the expected SHA-256 hash:

```bash
# Hardcoded SHA-256 checksums for scrut v0.4.3 release tarballs.
# scrut upstream does not publish checksum files, so these are computed
# from the release artifacts and must be updated when VERSION changes.
case "${os}-${arch}" in
  linux-x86_64)  expected="<hash>" ;;
  linux-aarch64) expected="<hash>" ;;
  macos-x86_64)  expected="<hash>" ;;
  macos-aarch64) expected="<hash>" ;;
  *)
    echo "No checksum available for ${os}-${arch}" >&2
    exit 1
    ;;
esac
```

After the `curl` download (line 41), before `tar` extraction (line 44), add the standard verification block (matching the pattern used by all other tools in the repo):

```bash
if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "${tarball_path}" | awk '{print $1}')"
else
  actual="$(shasum -a 256 "${tarball_path}" | awk '{print $1}')"
fi
if [ "${expected}" != "${actual}" ]; then
  echo "Checksum verification failed for ${tarball}" >&2
  echo "Expected: ${expected}" >&2
  echo "Actual:   ${actual}" >&2
  exit 1
fi
```

Remove the old comment (`# scrut upstream does not publish checksum files...`).

### Step 3: Update `.github/workflows/go-ci.yml` (scrut job, lines 243-275)

Apply identical changes to the duplicated scrut install step. This duplication is intentional (reusable workflows must be self-contained since consuming repos can't access local composite actions).

### Step 4: Update `.github/copilot-instructions.md`

Replace the scrut bullet (line 11) to reflect the new hardcoded checksum approach. The updated instruction should note:

- Scrut uses hardcoded checksums because upstream does not publish checksum files
- When bumping the scrut version, all 4 platform checksums must be recomputed
- Both `actions/setup-scrut/action.yml` and `.github/workflows/go-ci.yml` must be updated together

## Files to modify

| File | Change |
|------|--------|
| `actions/setup-scrut/action.yml` | Add checksum case statement and verification block |
| `.github/workflows/go-ci.yml` | Add identical checksum logic in scrut job |
| `.github/copilot-instructions.md` | Update scrut bullet to document hardcoded approach |

## Reference files (patterns to follow)

- `actions/setup-goreleaser/action.yml` (lines 41-62): canonical checksum verification block
- `actions/setup-actionlint/action.yml`: another consistent example

## Verification

1. Run `sha256sum` on each downloaded tarball to confirm hashes match the hardcoded values
2. Push branch and verify CI passes (the repo's own CI runs `github-lint` via actionlint)
3. Optionally test with a deliberately wrong checksum to confirm the failure path works
