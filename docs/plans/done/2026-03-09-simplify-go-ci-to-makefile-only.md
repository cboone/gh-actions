# 2026-03-09 Simplify go-ci.yml to Makefile-Only

## Context

Phase 4 (consuming repo migration) is complete. All 9 Go repos are live on
`go-ci.yml@v1` using direct Go commands. The `use-makefile` boolean input was
added on this branch (ddcb48c) but no repo has adopted it yet.

The goal is to make Makefile targets the only execution path in go-ci.yml,
removing the toggle and all direct-command fallbacks. Since all 9 repos are
already calling the workflow, this is a breaking change requiring a coordinated
rollout: prepare Makefiles, release v2.0.0, then update consuming repos to @v2.

## Scope (this branch, this repo)

1. Simplify `go-ci.yml` to always use `make` targets
2. Move Phase 4 plan from `docs/plans/todo/` to `docs/plans/done/`
3. Update README, CHANGELOG, CLAUDE.md, copilot-instructions.md
4. Create issues in `cboone-cc-plugins` for template/skill updates

Consuming repo Makefile prep and @v2 migration are separate efforts tracked by
their own issues/branches.

## Makefile Target Audit

The workflow will expect these targets: `vet`, `test`, `lint`, `build`, `fmt`.

| Repo         | vet     | test | lint     | build | fmt        | Needs Work       |
| ------------ | ------- | ---- | -------- | ----- | ---------- | ---------------- |
| gh-problemas | ok      | ok   | ok       | ok    | ok (check) | None             |
| fm           | ok      | ok   | n/a      | ok    | ok (check) | None             |
| stipple      | ok      | ok   | ok       | ok    | WRITES     | Fix fmt          |
| xylem        | ok      | ok   | ok       | ok    | WRITES     | Fix fmt          |
| snappy       | ok      | ok   | UMBRELLA | ok    | WRITES     | Fix lint + fmt   |
| bopca        | MISSING | ok   | ok       | ok    | WRITES     | Add vet, fix fmt |
| right-round  | MISSING | ok   | ok       | ok    | MISSING    | Add vet + fmt    |
| quod         | ok      | ok   | MISSING  | ok    | MISSING    | Add lint + fmt   |
| tracker      | none    | none | none     | none  | none       | Create Makefile  |

## Design Decisions

### `make fmt` must be a format check

Convention: `make fmt` exits non-zero when files need formatting (a check).
Repos that want a write-mode target should use `make format`.

Pattern:

```makefile
fmt: ## Check formatting (exits non-zero if files need formatting)
 @test -z "$$(gofmt -l .)" || { gofmt -l . && exit 1; }
```

### `make lint` must run only Go linting

Convention: `make lint` calls only `golangci-lint run ./...`. Repos with broader
lint targets should use `lint-all` as the umbrella.

### Coverage path stays direct

When `coverage: true`, the workflow still uses direct
`go test -v $test-flags -coverprofile=... ./...`. Only bopca uses coverage.

### Remove `build-flags` input

Only used in the direct `go build $build-flags ./...` path. No consuming repo
passes it.

### Keep `test-flags` for coverage only

Update its description to note it only applies when `coverage: true`.

### Versioning: v2.0.0

Removing `build-flags`, removing `use-makefile`, and changing test/lint/build/fmt
behavior from direct commands to Makefile targets is a breaking change per the
README versioning policy. Consuming repos on `@v1` are unaffected until they
switch to `@v2`.

## Implementation

### Step 1: Simplify go-ci.yml

**File: `.github/workflows/go-ci.yml`**

1. Remove inputs: `use-makefile` (lines 56-63), `build-flags` (lines 72-75)

2. Update `test-flags` description to:
   `Flags for go test (only used when coverage is enabled).`

3. Test job:
   - Remove "Run go vet" step (direct command, lines 118-120)
   - Remove `if` guard from "Run make vet" (line 123); rename to "Run vet"
   - Remove "Run tests" step (direct command, lines 126-128)
   - Remove `if` guard from "Run make test" (line 131); change condition to
     `if: ${{ !inputs.coverage }}`; rename to "Run tests"
   - Keep coverage steps unchanged

4. Lint job:
   - Remove "Run golangci-lint" step (direct, lines 251-253)
   - Remove `if` guard from "Run make lint" (line 256); rename to "Run lint"

5. Build job:
   - Remove "Build" step (direct, lines 274-276)
   - Remove `if` guard from "Run make build" (line 279); rename to "Build"

6. Format-check job:
   - Remove "Check gofmt" step (lines 399-407)
   - Remove "Check goimports" step (lines 409-418)
   - Remove `if` guard from "Run make fmt" (line 421); rename to
     "Check formatting"

### Step 2: Update README.md

- Remove `build-flags` from the go-ci inputs table
- Update `test-flags` description
- Update `run-format-check` description to reference `make fmt`
- Add note about Makefile target requirements in the go-ci section
- Add missing scrut inputs to the table (`scrut-build-cmd`, `scrut-env`,
  `scrut-test-dir`, `scrut-setup-cmd`)

### Step 3: Update CHANGELOG.md

Add to `[Unreleased]`:

```markdown
### Changed

- go-ci.yml now requires consuming repos to have a Makefile with targets:
  `vet`, `test`, and optionally `lint`, `build`, `fmt` (matching enabled jobs)
- go-ci.yml test job runs `make vet` and `make test` instead of direct Go
  commands
- go-ci.yml lint job runs `make lint` instead of `golangci-lint run ./...`
- go-ci.yml build job runs `make build` instead of `go build`
- go-ci.yml format-check job runs `make fmt` instead of inline gofmt/goimports
- go-ci.yml `test-flags` input now only applies when `coverage` is enabled
- Updated `actions/setup-go` from v5 to v6 across go-ci.yml and go-release.yml

### Removed

- go-ci.yml `use-makefile` input (Makefile is now the only execution mode)
- go-ci.yml `build-flags` input (build flags belong in each repo's Makefile)
```

### Step 4: Update CLAUDE.md

Add to Key Conventions:

```markdown
### Makefile Target Convention for go-ci.yml

Consuming Go repos must provide Makefile targets for each enabled go-ci.yml
job: `vet`, `test`, `lint`, `build`, `fmt`. The `fmt` target must be a format
check (exit non-zero on unformatted code), not a write operation.
```

### Step 5: Update copilot-instructions.md

Add bullet about go-ci.yml Makefile target requirements.

### Step 6: Move Phase 4 plan to done

Move `docs/plans/todo/2026-03-08-phase-4-consuming-repo-migration.md` to
`docs/plans/done/`.

### Step 7: Create issues in cboone-cc-plugins

Create GitHub issues for updating templates, skills, and commands that scaffold
new Go repos to include the required Makefile targets and use `go-ci.yml@v2`:

1. **Update Go project Makefile template**: Ensure the `scaffold-go-cli` skill
   and any Go project templates include a Makefile with the standard targets
   (`vet`, `test`, `lint`, `build`, `fmt`) using the correct conventions (fmt as
   check, lint as golangci-lint only).

2. **Update Go CI workflow template**: Update any templates or skills that
   generate `.github/workflows/ci.yml` for Go projects to reference
   `go-ci.yml@v2` (once released) and remove `build-flags` / `use-makefile`
   inputs.

3. **Document Makefile conventions**: Add documentation to relevant skills about
   the `make fmt` check convention and `make lint` Go-only convention.

## Execution Order

```text
1. Steps 1-6: All changes in this repo on this branch
   - Commit go-ci.yml simplification
   - Commit doc updates (README, CHANGELOG, CLAUDE.md, copilot-instructions)
   - Move Phase 4 plan to done/

2. Step 7: Create issues in cboone-cc-plugins

3. Merge this branch to main (requires merge from main first since
   v1.0.0 release commit is on main)

4. Release v2.0.0, create floating v2 tag
   - Consuming repos on @v1 remain unaffected

5. Consuming repo work (separate branches, 7 repos need Makefile prep):
   - right-round: add vet, fmt
   - quod: add lint, fmt
   - tracker: create Makefile
   - bopca: add vet, fix fmt to check
   - stipple: fix fmt to check
   - xylem: fix fmt to check
   - snappy: narrow lint to Go-only, fix fmt to check

6. Update consuming repos from @v1 to @v2 (after Makefiles are ready)
```

Steps 5 and 6 can be combined per repo (Makefile fix + @v2 migration in one PR).

## Verification

### go-ci.yml changes

- Run `actionlint` on the modified workflow
- Verify no references to `use-makefile` or `build-flags` remain
- Grep for `inputs.use-makefile` and `inputs.build-flags` returns nothing
- Test job steps: `make vet`, `make test` (non-coverage),
  `go test ... -coverprofile` (coverage)
- Lint job steps: golangci-lint install, `make lint`
- Build job steps: `make build`
- Format-check job steps: `make fmt`

### Post-release consuming repo migration

For each repo after Makefile prep:

- `make vet`, `make test`, `make lint`, `make build` pass locally
- `make fmt` exits 0 on clean code, exits 1 after breaking formatting
- Push branch with @v2 ref, confirm all CI jobs pass
