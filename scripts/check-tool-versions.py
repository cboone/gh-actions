#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Check pinned tool versions against upstream latest stable releases.

Covers tools that Dependabot does not track: version strings inside
workflow `env:` blocks and `inputs.*-version` defaults, plus the
hardcoded SHA-256 checksum tables for shellcheck, shfmt, scrut,
cargo-audit, and cargo-llvm-cov.

Exit status is 0 when everything is current, 1 when at least one tool
has a newer upstream release, 2 on lookup errors. Outputs a Markdown
report to stdout suitable for piping into a GitHub issue body.

Uses only the Python standard library so the script has no third-party
dependencies and cannot be compromised by a tampered package registry.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HTTP_TIMEOUT = 30


@dataclass(frozen=True)
class Tool:
    name: str
    current: str
    fetch_latest: Callable[[], str]
    notes: str = ""


def _gh_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """GET a URL and return parsed JSON. Raises RuntimeError with the HTTP status on non-2xx responses."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc


def github_latest_release(repo: str) -> str:
    """Latest non-prerelease release tag with leading 'v' stripped."""
    data = _get_json(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers=_gh_headers(),
    )
    return data["tag_name"].lstrip("v")


def github_latest_matching(repo: str, pattern: str) -> str:
    """Latest non-prerelease release tag matching pattern; returns capture group 1."""
    data = _get_json(
        f"https://api.github.com/repos/{repo}/releases?per_page=50",
        headers=_gh_headers(),
    )
    rx = re.compile(pattern)
    for release in data:
        if release.get("prerelease") or release.get("draft"):
            continue
        m = rx.fullmatch(release["tag_name"])
        if m:
            return m.group(1)
    raise RuntimeError(f"no release tag matched {pattern!r} in {repo}")


def pypi_latest(package: str) -> str:
    data = _get_json(f"https://pypi.org/pypi/{package}/json")
    return data["info"]["version"]


def nodejs_lts_latest(major: int) -> str:
    data = _get_json("https://nodejs.org/dist/index.json")
    for entry in data:
        version = entry["version"].lstrip("v")
        if int(version.split(".", 1)[0]) == major and entry.get("lts"):
            return version
    raise RuntimeError(f"no Node {major} LTS release")


# Hardcoded current pinned versions. Update these together with the
# workflow / action / Makefile / requirements.txt files when bumping.
TOOLS: list[Tool] = [
    Tool(
        "actionlint",
        "1.7.12",
        lambda: github_latest_release("rhysd/actionlint"),
        notes=(
            "On bump, check whether it recognizes the `job.workflow_*` context "
            "properties; if it does, delete `.github/actionlint.yaml`, which "
            "exists only to suppress that false positive. run-ci.yml's wrapper "
            "check asserts the set-up-actionlint default version; bump it too."
        ),
    ),
    Tool("golangci-lint", "2.11.4", lambda: github_latest_release("golangci/golangci-lint")),
    Tool("gitleaks", "8.30.1", lambda: github_latest_release("gitleaks/gitleaks")),
    Tool("trufflehog", "3.95.2", lambda: github_latest_release("trufflesecurity/trufflehog")),
    Tool("goreleaser", "2.15.4", lambda: github_latest_release("goreleaser/goreleaser")),
    Tool("markscribe", "0.8.1", lambda: github_latest_release("charmbracelet/markscribe")),
    Tool("codecov CLI", "11.2.8", lambda: github_latest_release("codecov/codecov-cli")),
    Tool("cargo-deny", "0.19.4", lambda: github_latest_release("EmbarkStudios/cargo-deny")),
    Tool(
        "cargo-nextest",
        "0.9.133",
        lambda: github_latest_matching("nextest-rs/nextest", r"cargo-nextest-(\d+\.\d+\.\d+)"),
    ),
    Tool(
        "uv",
        "0.11.8",
        lambda: github_latest_release("astral-sh/uv"),
        notes=(
            "Bump every pin together: UV_VERSION in lint-text.yml and "
            "check-tool-versions.yml, the uv-version default in run-reuse's "
            "action.yml and in run-scrut-tests.yml, and both the install and the "
            "asserted version in run-ci.yml. The documented defaults have to match: "
            "the input tables in actions/run-reuse/README.md and "
            "docs/workflows/run-scrut-tests.md, and the example in "
            "actions/install-pinned-tool/README.md. Grep the outgoing version to "
            "catch any that moved; CHANGELOG entries are historical and stay."
        ),
    ),
    Tool(
        "scrut",
        "0.4.3",
        lambda: github_latest_release("facebookincubator/scrut"),
        "Audit all four native release assets before updating their SHA-256 pins. "
        "Linux arm64 and macOS x86-64 currently build from pinned source: update "
        "the source commit, archive hash, reviewed Cargo.lock, Rust compiler, "
        "version script and installation spec together, across set-up-scrut "
        "and run-scrut-tests/run-go-ci/run-zig-ci. See "
        "docs/scrut-installation-investigation.md for removal criteria.",
    ),
    Tool(
        "shellcheck",
        "0.11.0",
        lambda: github_latest_release("koalaman/shellcheck"),
        "Committed SHA-256 lines must be regenerated on bump: the `checksums` "
        "default in actions/set-up-shellcheck and `shellcheck-checksums` in "
        "lint-shell.yml and lint-github-actions.yml. run-ci.yml installs "
        "shellcheck directly and through the wrapper and asserts the version "
        "in both checks; bump its four lines and both specs too.",
    ),
    Tool(
        "shfmt",
        "3.14.1",
        lambda: github_latest_release("mvdan/sh"),
        "Committed SHA-256 lines must be regenerated on bump: the `checksums` "
        "default in actions/set-up-shfmt and `shfmt-checksums` in lint-shell.yml. "
        "run-ci.yml's wrapper check asserts the set-up-shfmt default version; "
        "bump it too. Its remaining shfmt 3.13.1 lines, and the 3.15.0 in its "
        "version-bumped-without-checksums rejection case, are test fixtures "
        "and can stay.",
    ),
    Tool(
        "cargo-audit",
        "0.22.1",
        lambda: github_latest_matching("rustsec/rustsec", r"cargo-audit/v(\d+\.\d+\.\d+)"),
        "Hardcoded SHA-256 checksums must be regenerated on bump.",
    ),
    Tool(
        "cargo-llvm-cov",
        "0.8.5",
        lambda: github_latest_release("taiki-e/cargo-llvm-cov"),
        "Hardcoded SHA-256 checksums must be regenerated on bump.",
    ),
    Tool("yamllint", "1.38.0", lambda: pypi_latest("yamllint"),
         "requirements/yamllint.txt must be regenerated with `uv pip compile --generate-hashes`."),
    Tool("reuse", "5.0.2", lambda: pypi_latest("reuse"),
         "requirements/reuse.txt must be regenerated with `uv pip compile --generate-hashes`."),
    Tool("Node.js LTS (24)", "24.15.0", lambda: nodejs_lts_latest(24)),
]


def main() -> int:
    outdated: list[tuple[Tool, str]] = []
    errors: list[tuple[Tool, str]] = []

    for tool in TOOLS:
        try:
            latest = tool.fetch_latest()
        except Exception as exc:
            errors.append((tool, f"{type(exc).__name__}: {exc}"))
            continue
        if latest != tool.current:
            outdated.append((tool, latest))

    if not outdated and not errors:
        print("All pinned tool versions are current.")
        return 0

    if outdated:
        print("# Outdated tool versions\n")
        print("| Tool | Current | Latest | Notes |")
        print("| --- | --- | --- | --- |")
        for tool, latest in outdated:
            print(f"| {tool.name} | `{tool.current}` | `{latest}` | {tool.notes} |")
        print()
    if errors:
        heading = "## Lookup errors" if outdated else "# Lookup errors"
        print(f"{heading}\n")
        for tool, msg in errors:
            print(f"- **{tool.name}**: {msg}")
        print()

    return 2 if errors else 1


if __name__ == "__main__":
    sys.exit(main())
