# Lint Tool Installers for Local Development

## Context

Issue #2: The `make lint` and `make lint-yaml` Makefile targets call `actionlint` and `yamllint` directly, but these tools are not managed via `devDependencies` (unlike `prettier`, `markdownlint-cli2`, and `cspell` which use `npx`). The targets fail on a clean machine without these tools pre-installed.

The goal is to make all Makefile lint targets self-bootstrapping, so `make lint` and `make lint-yaml` work on a clean machine with minimal prerequisites.

## Approach

Two different strategies, matching each tool's ecosystem:

1. **yamllint** (Python): Switch to `uv tool run`, which auto-fetches and caches the pinned version on demand (analogous to `npx` for Node.js tools). Already used in `text-lint.yml`.
2. **actionlint** (Go binary): Auto-download the binary to `.local/bin/` as a Make file target prerequisite. Uses the same download/checksum/extract pattern as `actions/setup-actionlint/action.yml`.

## Changes

### 1. Create `scripts/install-actionlint.sh` (new file)

Shell script that downloads, verifies, and installs the actionlint binary locally.

- Accept `VERSION` and `INSTALL_DIR` environment variables (with defaults: `1.7.11` and `.local/bin`)
- Detect OS via `uname -s` (linux/darwin)
- Detect architecture via `uname -m` (amd64/arm64)
- Download tarball from GitHub releases
- Verify SHA-256 checksum (support both `sha256sum` and `shasum -a 256`)
- Extract binary to `INSTALL_DIR`
- Clean up temporary files
- Skip download if binary already exists at correct version
- Follow the exact pattern from `actions/setup-actionlint/action.yml` (lines 18-62)

### 2. Update `Makefile`

- Add version variables at top: `ACTIONLINT_VERSION := 1.7.11`, `YAMLLINT_VERSION := 1.37.1`
- Add `ACTIONLINT := .local/bin/actionlint` path variable
- Add `$(ACTIONLINT)` file target that calls the install script with version/dir from Makefile vars
- Make `lint` depend on `$(ACTIONLINT)` and invoke `$(ACTIONLINT)` instead of bare `actionlint`
- Change `lint-yaml` to use `uv tool run --from "yamllint==$(YAMLLINT_VERSION)" yamllint .`
- Add `setup` phony target that depends on `$(ACTIONLINT)` (bootstrap entry point)
- Update `.PHONY` line to include `setup`

### 3. Update `.gitignore`

Add `.local/` entry (for the downloaded binary directory).

### 4. Update `README.md`

Fill in the `Installation` and `Usage` TODO placeholders:

- **Prerequisites**: Node.js >= 20.18, uv, curl
- **Setup**: `npm install` for Node.js dev dependencies, `make setup` for binary tools
- **Targets**: Document all Makefile targets

### 5. Update `cspell.json` (if needed)

Check whether new words from README/script changes need to be added.

## Key Files

| File                            | Action          | Reference                                               |
| ------------------------------- | --------------- | ------------------------------------------------------- |
| `scripts/install-actionlint.sh` | Create          | Pattern from `actions/setup-actionlint/action.yml`      |
| `Makefile`                      | Modify          | Current file has bare `actionlint` and `yamllint` calls |
| `.gitignore`                    | Modify          | Add `.local/`                                           |
| `README.md`                     | Modify          | Fill TODO sections                                      |
| `cspell.json`                   | Possibly modify | New words if needed                                     |

## Version Pinning

| Tool              | Version | Local Invocation                        | CI Counterpart                         |
| ----------------- | ------- | --------------------------------------- | -------------------------------------- |
| actionlint        | 1.7.11  | `.local/bin/actionlint` via Makefile    | `github-lint.yml` / `setup-actionlint` |
| yamllint          | 1.37.1  | `uv tool run --from "yamllint==1.37.1"` | `text-lint.yml` env var                |
| prettier          | 3.8.1   | `npx prettier`                          | `text-lint.yml` npm install            |
| markdownlint-cli2 | 0.21.0  | `npx markdownlint-cli2`                 | `text-lint.yml` npm install            |
| cspell            | 9.7.0   | `npx cspell`                            | `text-lint.yml` npm install            |

## Verification

1. Remove `.local/` if it exists, then run `make lint` -- should auto-download actionlint and succeed
2. Run `make lint-yaml` -- should auto-fetch yamllint via `uv tool run` and succeed
3. Run `make setup` -- should install actionlint to `.local/bin/`
4. Run `make lint` a second time -- should reuse existing binary (no re-download)
5. Run `make format-check`, `make lint-md`, `make spell` -- should still work unchanged
6. Run linters on the changed files themselves (the install script, Makefile, README)
