# Fix markscribe tar extraction (issue #28)

## Context

The `run-markscribe` action fails because charmbracelet/markscribe release
tarballs contain files under a versioned directory prefix (e.g.,
`markscribe_0.8.1_Linux_x86_64/markscribe`). The current extraction command
expects a bare `markscribe` at the archive root, causing tar to fail with
"Not found in archive".

## Change

**File:** `actions/run-markscribe/action.yml`, line 69

Replace:

```bash
tar -xz -C "${install_dir}" -f "${archive_path}" markscribe
```

With:

```bash
tar -xz -C "${install_dir}" -f "${archive_path}" --strip-components=1
```

This strips the top-level versioned directory prefix, extracting the
`markscribe` binary (plus LICENSE and README.md, which are harmless) directly
into `${install_dir}`. This matches the existing pattern used by `setup-scrut`
(`actions/setup-scrut/action.yml:79`) and several workflows (`scrut.yml`,
`zig-ci.yml`, `go-ci.yml`).

## Verification

- The action only runs on GitHub Actions runners, so local testing is limited.
- Verify the change is consistent with the `--strip-components=1` pattern
  already used elsewhere in the repo.
- A downstream repo that uses `run-markscribe` (e.g., cboone/cboone) can
  trigger a workflow run to confirm the fix.
