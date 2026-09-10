#!/usr/bin/env bash
# pin-exact-versions.sh -- Update consuming repos from @v1/@v2 to exact version tags.
#
# Creates a plain git worktree in /tmp for each repo, applies sed replacements,
# commits, pushes, and opens a PR. The primary local checkout is never modified.
#
# Usage:
#   ./scripts/pin-exact-versions.sh              # Process all repos
#   ./scripts/pin-exact-versions.sh fm snappy     # Process only named repos

set -euo pipefail

readonly TARGET_VERSION="v2.1.2"
readonly BRANCH="chore/pin-exact-version-tags"
readonly COMMIT_MSG="chore: pin gh-actions references to exact version ${TARGET_VERSION}"
readonly DEV_DIR="${HOME}/Development"
readonly WORK_DIR="/tmp/pin-exact-versions"

readonly ALL_REPOS=(
  claude-dotfiles dotfiles pb-bug
  cboone-alpine-plugins cboone-tailwind-plugins
  snappy-sh-site bopca-sh-site tmux-binding-help
  compbox cboone-cc-plugins pbcopy2
  right-round gh-problemas stipple tracker quod
  fm xylem bopca snappy
)

readonly PR_BODY="Pin all \`cboone/gh-actions\` workflow and action references from floating
tags (\`@v1\`, \`@v2\`) to the exact version \`@${TARGET_VERSION}\`.

Part of the migration to exact-version-only tagging (cboone/gh-actions#25).
After all consuming repos are updated, the floating \`v1\` and \`v2\` tags
will be deleted from the gh-actions remote."

succeeded=()
skipped=()
failed=()

function process_repo() {
  local repo="$1"
  local repo_dir="${DEV_DIR}/${repo}"
  local wt_dir="${WORK_DIR}/${repo}"

  echo ""
  echo "=== ${repo} ==="

  if [[ ! -d "${repo_dir}/.git" ]] && [[ ! -f "${repo_dir}/.git" ]]; then
    echo "  SKIP: no local checkout at ${repo_dir}"
    skipped+=("${repo}: no local checkout")
    return
  fi

  # Clean up any prior worktree at this path
  if [[ -d "${wt_dir}" ]]; then
    git -C "${repo_dir}" worktree remove "${wt_dir}" --force 2>/dev/null || rm -rf "${wt_dir}"
  fi

  # Delete the branch if it already exists locally
  git -C "${repo_dir}" branch -D "${BRANCH}" 2>/dev/null || true

  # Fetch latest
  echo "  Fetching origin..."
  git -C "${repo_dir}" fetch origin --quiet

  # Create worktree from origin/main
  echo "  Creating worktree at ${wt_dir}..."
  git -C "${repo_dir}" worktree add "${wt_dir}" -b "${BRANCH}" origin/main --quiet

  # Run sed replacements
  local wf_dir="${wt_dir}/.github/workflows"
  if [[ ! -d "${wf_dir}" ]]; then
    echo "  SKIP: no .github/workflows/ directory"
    git -C "${repo_dir}" worktree remove "${wt_dir}" --force 2>/dev/null || true
    git -C "${repo_dir}" branch -D "${BRANCH}" 2>/dev/null || true
    skipped+=("${repo}: no workflows directory")
    return
  fi

  # Replace @v1 and @v2 with @TARGET_VERSION on lines referencing cboone/gh-actions.
  # Use find instead of globs to avoid BSD sed failing on unmatched patterns.
  find "${wf_dir}" -type f \( -name '*.yml' -o -name '*.yaml' \) \
    -exec sed -i '' "s|cboone/gh-actions\(.*\)@v1\$|cboone/gh-actions\1@${TARGET_VERSION}|" {} +
  find "${wf_dir}" -type f \( -name '*.yml' -o -name '*.yaml' \) \
    -exec sed -i '' "s|cboone/gh-actions\(.*\)@v2\$|cboone/gh-actions\1@${TARGET_VERSION}|" {} +

  # Check if anything changed
  if git -C "${wt_dir}" diff --quiet; then
    echo "  SKIP: no floating tag references found"
    git -C "${repo_dir}" worktree remove "${wt_dir}" --force 2>/dev/null || true
    git -C "${repo_dir}" branch -D "${BRANCH}" 2>/dev/null || true
    skipped+=("${repo}: no changes needed")
    return
  fi

  # Show what changed
  echo "  Changes:"
  git -C "${wt_dir}" diff --stat | sed 's/^/    /'

  # Stage, commit, push
  git -C "${wt_dir}" add .github/workflows/
  git -C "${wt_dir}" commit -S -m "${COMMIT_MSG}" --quiet

  echo "  Pushing..."
  if ! git -C "${wt_dir}" push -u origin "${BRANCH}" --quiet 2>&1; then
    echo "  FAIL: push failed"
    failed+=("${repo}: push failed")
    return
  fi

  # Create PR
  echo "  Creating PR..."
  local pr_url
  pr_url=$(gh pr create \
    --repo "cboone/${repo}" \
    --head "${BRANCH}" \
    --title "chore: pin gh-actions to ${TARGET_VERSION}" \
    --body "${PR_BODY}" 2>&1) || true

  if [[ "${pr_url}" == http* ]]; then
    echo "  PR: ${pr_url}"
    succeeded+=("${repo}: ${pr_url}")
  else
    echo "  WARN: PR creation returned: ${pr_url}"
    failed+=("${repo}: PR creation issue - ${pr_url}")
  fi

  # Clean up worktree (branch stays for the PR)
  git -C "${repo_dir}" worktree remove "${wt_dir}" --force 2>/dev/null || true
}

function main() {
  local repos=("${ALL_REPOS[@]}")
  if [[ $# -gt 0 ]]; then
    repos=("$@")
  fi

  mkdir -p "${WORK_DIR}"

  echo "Pinning cboone/gh-actions references to @${TARGET_VERSION}"
  echo "Repos: ${#repos[@]}"

  for repo in "${repos[@]}"; do
    process_repo "${repo}"
  done

  echo ""
  echo "==============================="
  echo "  Summary"
  echo "==============================="
  echo ""
  echo "Succeeded (${#succeeded[@]}):"
  for entry in "${succeeded[@]+"${succeeded[@]}"}"; do
    echo "  ${entry}"
  done
  echo ""
  echo "Skipped (${#skipped[@]}):"
  for entry in "${skipped[@]+"${skipped[@]}"}"; do
    echo "  ${entry}"
  done
  echo ""
  echo "Failed (${#failed[@]}):"
  for entry in "${failed[@]+"${failed[@]}"}"; do
    echo "  ${entry}"
  done

  # Clean up work directory if empty
  rmdir "${WORK_DIR}" 2>/dev/null || true
}

main "$@"
