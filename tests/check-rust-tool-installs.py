#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Exercise run-rust-ci's cargo-audit and cargo-llvm-cov install blocks.

These two tools install from release archives whose upstreams publish no
checksum file, so the workflow carries the digests itself, keyed by
version and target triple. Nothing else in CI runs run-rust-ci.yml, so
this is the only coverage for that lookup and for the verification it
guards.

Each tool is checked three ways: the committed defaults install and
report the pinned version; a version with no matching entry is refused
before anything is downloaded; and a tampered digest is refused after it
is. The last two are the controls that would catch the lookup silently
accepting an archive it never verified.
"""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/run-rust-ci.yml"

TOOLS = {
    "cargo-audit": {
        "step": "Install cargo-audit",
        "version_input": "audit-version",
        "checksums_input": "audit-checksums",
        "binary": "cargo-audit",
        "bin_dir": "cargo-audit-bin",
        "version_args": ["--version"],
    },
    "cargo-llvm-cov": {
        "step": "Install cargo-llvm-cov",
        "version_input": "llvm-cov-version",
        "checksums_input": "llvm-cov-checksums",
        "binary": "cargo-llvm-cov",
        "bin_dir": "cargo-llvm-cov-bin",
        "version_args": ["llvm-cov", "--version"],
    },
}


def run_block(step_name):
    """Read a named step's literal run block without a YAML dependency."""
    step = WORKFLOW.read_text().split(f"      - name: {step_name}\n", 1)[1]
    step = step.split("      - name:", 1)[0]
    lines = step.split("        run: |\n", 1)[1].splitlines()
    body = []
    for line in lines:
        if line and not line.startswith("          "):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body))


def input_default(name):
    """Read a workflow_call input's literal block default."""
    text = WORKFLOW.read_text().split(f"      {name}:\n", 1)[1]
    lines = text.split("        default: |\n", 1)[1].splitlines()
    body = []
    for line in lines:
        if line and not line.startswith("          "):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body)).strip("\n")


def input_version(name):
    """Read a workflow_call input's quoted scalar default."""
    text = WORKFLOW.read_text().split(f"      {name}:\n", 1)[1]
    match = re.search(r'^        default: "([^"]+)"$', text, re.M)
    assert match, f"no quoted default for {name}"
    return match.group(1)


def execute(step_name, runner_temp, version, checksums):
    # The step inherits the runner's environment, proxy settings included,
    # so the block is given the same rather than a stripped one.
    env = {
        **os.environ,
        "RUNNER_TEMP": str(runner_temp),
        "GITHUB_PATH": str(runner_temp / "github-path"),
        "VERSION": version,
        "CHECKSUMS": checksums,
    }
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", run_block(step_name)],
        env=env,
        capture_output=True,
        text=True,
    )


def check(tool, spec):
    version = input_version(spec["version_input"])
    checksums = input_default(spec["checksums_input"])
    failures = []

    with tempfile.TemporaryDirectory() as tmp:
        runner_temp = Path(tmp)
        result = execute(spec["step"], runner_temp, version, checksums)
        installed = runner_temp / spec["bin_dir"] / spec["binary"]
        if result.returncode != 0:
            failures.append(
                f"{tool}: committed defaults failed to install "
                f"(exit {result.returncode})\n{result.stderr.strip()}"
            )
        elif not installed.is_file():
            failures.append(f"{tool}: install reported success but {installed} is absent")
        else:
            reported = subprocess.run(
                [str(installed), *spec["version_args"]],
                capture_output=True,
                text=True,
            )
            combined = f"{reported.stdout} {reported.stderr}".replace("\n", " ")
            if version not in combined:
                failures.append(
                    f"{tool}: installed binary reports '{combined.strip()}', "
                    f"expected {version}"
                )
            else:
                print(f"  {tool}: committed defaults install and report {version}")

    # A version the table does not cover must be refused, and must be
    # refused before the archive is fetched.
    with tempfile.TemporaryDirectory() as tmp:
        runner_temp = Path(tmp)
        absent = "0.0.1"
        result = execute(spec["step"], runner_temp, absent, checksums)
        want = f"No checksum entry for {tool} {absent}"
        downloads = [p for p in runner_temp.iterdir() if p.suffix in {".tgz", ".gz"}]
        if result.returncode == 0:
            failures.append(f"{tool}: accepted version {absent} with no checksum entry")
        elif want not in result.stderr:
            failures.append(
                f"{tool}: refused {absent} without reporting '{want}'\n"
                f"{result.stderr.strip()}"
            )
        elif downloads:
            failures.append(
                f"{tool}: fetched {[p.name for p in downloads]} before resolving a digest"
            )
        else:
            print(f"  {tool}: unknown version refused before any download")

    # A digest that does not match the archive must be refused too, which
    # is what proves the lookup feeds a verification rather than decorating
    # one.
    with tempfile.TemporaryDirectory() as tmp:
        runner_temp = Path(tmp)
        tampered = re.sub(r"^[0-9a-f]{64}", "0" * 64, checksums, flags=re.M)
        result = execute(spec["step"], runner_temp, version, tampered)
        if result.returncode == 0:
            failures.append(f"{tool}: accepted an archive whose digest did not match")
        elif "Checksum verification failed" not in result.stderr:
            failures.append(
                f"{tool}: rejected a tampered digest without reporting a checksum "
                f"failure\n{result.stderr.strip()}"
            )
        else:
            print(f"  {tool}: tampered digest rejected after download")

    return failures


def main():
    failures = []
    for tool, spec in TOOLS.items():
        failures.extend(check(tool, spec))

    if failures:
        for failure in failures:
            print(f"::error::{failure}", file=sys.stderr)
        return 1
    print("run-rust-ci tool installs verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
