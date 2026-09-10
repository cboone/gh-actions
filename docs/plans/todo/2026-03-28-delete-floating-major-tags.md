# Delete Floating Major Tags (v1, v2)

## Context

Issue: cboone/gh-actions#25

The gh-actions repo previously maintained floating major tags (`v1`, `v2`) that
were force-updated on each release. PR #27 merged documentation changes removing
all floating tag references and recommending exact version pins. The floating
tags themselves still exist on the remote, pointing at stale commits (`v1` at
v1.0.0, `v2` at v2.1.0).

Before deleting these tags, all 20 consuming repos that reference `@v1` or `@v2`
must be updated to the exact version `@v2.1.2`. Deleting the tags without this
prerequisite would break CI across all downstream repos.

## Current state of consuming repos

Every consuming repo was audited via the GitHub API on 2026-03-28. The `cboone`
profile README repo already references `@v2.1.2` and needs no changes.

### Repos using `@v1` only (11 repos)

| Repo                    | Workflow(s)   | References                                   |
| ----------------------- | ------------- | -------------------------------------------- |
| claude-dotfiles         | gitleaks.yml  | `secret-scan.yml@v1`                         |
| dotfiles                | gitleaks.yml  | `secret-scan.yml@v1`                         |
| pb-bug                  | gitleaks.yml  | `secret-scan.yml@v1`                         |
| compbox                 | ci.yml        | `text-lint.yml@v1`, `scrut.yml@v1`           |
| cboone-cc-plugins       | ci.yml        | `setup-shfmt@v1`, `setup-actionlint@v1`      |
| cboone-alpine-plugins   | publish.yml   | `npm-publish.yml@v1`                         |
| cboone-tailwind-plugins | publish.yml   | `npm-publish.yml@v1`                         |
| snappy-sh-site          | deploy.yml    | `pages-deploy.yml@v1`                        |
| bopca-sh-site           | deploy.yaml   | `pages-deploy.yml@v1`                        |
| pbcopy2                 | ci.yml        | `setup-actionlint@v1`, `setup-scrut@v1`      |
| tmux-binding-help       | scrut.yml     | `setup-scrut@v1`                             |

### Repos using both `@v1` and `@v2` (7 repos)

| Repo          | `@v2` refs             | `@v1` refs                                                                           |
| ------------- | ---------------------- | ------------------------------------------------------------------------------------ |
| fm            | `go-ci.yml@v2`         | `secret-scan.yml@v1`, `go-release.yml@v1`                                            |
| snappy        | `go-ci.yml@v2`         | `text-lint.yml@v1`, `shell-lint.yml@v1`, `github-lint.yml@v1`, `setup-scrut@v1`, `go-release.yml@v1` |
| bopca         | `go-ci.yml@v2`         | `secret-scan.yml@v1`, `go-release.yml@v1`                                            |
| xylem         | `go-ci.yml@v2`         | `text-lint.yml@v1`, `github-lint.yml@v1`, `go-release.yml@v1`                        |
| right-round   | `go-ci.yml@v2`         | `go-release.yml@v1`                                                                  |
| gh-problemas  | `go-ci.yml@v2`         | `go-release.yml@v1`                                                                  |
| stipple       | `go-ci.yml@v2`         | `go-release.yml@v1`                                                                  |

### Repos using `@v2` only (2 repos)

| Repo    | Workflow   | Reference        |
| ------- | ---------- | ---------------- |
| tracker | test.yaml  | `go-ci.yml@v2`   |
| quod    | ci.yml     | `go-ci.yml@v2`   |

### Compatibility

All migrations are safe. The only breaking change in v2.0.0 was `go-ci.yml`
requiring Makefile targets, and every repo using `go-ci.yml` already references
`@v2`. All other workflows and composite actions are backward compatible between
v1 and v2.1.2.

## Changes

### 1. Create migration script

Create `scripts/pin-exact-versions.sh` in this repo (on the
`fix/remove-floating-tags` branch). This is a throwaway script that does not
need to be merged to main.

The script iterates over each consuming repo and:

1. Validates a local checkout exists at `~/Development/<repo>`
2. Ensures the working tree is clean
3. Fetches and checks out main
4. Creates branch `chore/pin-exact-version-tags`
5. Runs sed to replace `@v1` and `@v2` with `@v2.1.2` in workflow files:
   ```bash
   sed -i '' 's|cboone/gh-actions\(.*\)@v1$|cboone/gh-actions\1@v2.1.2|' \
     .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null
   sed -i '' 's|cboone/gh-actions\(.*\)@v2$|cboone/gh-actions\1@v2.1.2|' \
     .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null
   ```
   The `$` anchor prevents matching refs that are already on exact versions
   (e.g., `@v2.1.2`).
6. Stages, commits (GPG-signed), and pushes
7. Creates a PR via `gh pr create`

Error handling: skip repos with dirty working trees, existing branches, or no
gh-actions references. Print a summary at the end.

**Repo list** (20 repos, in order from simplest to most complex):

```text
claude-dotfiles dotfiles pb-bug
cboone-alpine-plugins cboone-tailwind-plugins
snappy-sh-site bopca-sh-site tmux-binding-help
compbox cboone-cc-plugins pbcopy2
right-round gh-problemas stipple tracker quod
fm xylem bopca snappy
```

### 2. Run the migration script

Execute the script to create PRs across all 20 repos. Wait for CI to pass on
each PR, then merge.

### 3. Verify no floating refs remain

Before deleting tags, run a verification sweep across all repos:

```bash
for repo in claude-dotfiles dotfiles pb-bug compbox cboone-cc-plugins \
  cboone-alpine-plugins cboone-tailwind-plugins snappy-sh-site bopca-sh-site \
  pbcopy2 tmux-binding-help fm snappy bopca xylem right-round gh-problemas \
  stipple tracker quod cboone; do
  result=$(gh api "repos/cboone/$repo/git/trees/main?recursive=1" \
    --jq '.tree[].path' 2>/dev/null \
    | grep -E '\.github/workflows/.*\.ya?ml$' \
    | while read wf; do
        gh api "repos/cboone/$repo/contents/$wf" --jq '.content' 2>/dev/null \
          | base64 -d 2>/dev/null \
          | grep -E 'cboone/gh-actions.*@v[12]$' 2>/dev/null
      done)
  if [ -n "$result" ]; then
    echo "BLOCKED: $repo still has floating refs"
  fi
done
```

### 4. Delete floating tags

In the gh-actions repo, delete the tags locally and from the remote:

```bash
git tag -d v1 v2
git push origin :refs/tags/v1 :refs/tags/v2
```

### 5. Verify deletion

```bash
# Confirm tags are gone from remote
git ls-remote --tags origin | grep -E 'refs/tags/v[12]$'
# Should return empty

# Confirm exact version tags still exist
git ls-remote --tags origin | grep 'v2.1.2'
# Should show v2.1.2
```

### 6. Spot-check CI

Trigger a workflow run in a few repos to confirm nothing broke:

```bash
for repo in claude-dotfiles compbox fm snappy; do
  gh workflow run ci.yml --repo "cboone/$repo" 2>/dev/null \
    || gh workflow run gitleaks.yml --repo "cboone/$repo" 2>/dev/null
done
```

## Files to create/modify

**In gh-actions (this repo):**

- `scripts/pin-exact-versions.sh` (new, throwaway migration script)

**In each of 20 consuming repos (automated by the script):**

- `.github/workflows/*.yml` / `*.yaml`: sed replacement of `@v1`/`@v2` with
  `@v2.1.2`

## Verification

1. Run the migration script; confirm PRs are created in all 20 repos
2. Wait for CI to pass on each PR
3. Merge all PRs
4. Run the verification sweep (step 3 above) to confirm no floating refs remain
5. Delete the tags (step 4 above)
6. Verify tags are gone (step 5 above)
7. Spot-check CI in a few repos (step 6 above)
