#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Exercise check-tool-versions.yml's actual Run version check block against stub audits."""

import os
import shlex
import subprocess
import tempfile
import textwrap
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github/workflows/check-tool-versions.yml"
)
STEP = "Run version check"
# The path the block invokes. A stand-in lives here for each case: the block
# reads an exit status and a stdout stream, and cares about neither the
# language the real audit is written in nor what it looked up.
AUDIT = "scripts/check-tool-versions.py"

# Stand-ins for what scripts/check-tool-versions.py prints on each of its three
# documented exits. Only the shape matters here; the content of a real report is
# the script's business.
CURRENT = "All pinned tool versions are current.\n"
OUTDATED = (
    "# Outdated tool versions\n\n"
    "| Tool | Current | Latest | Notes |\n"
    "| --- | --- | --- | --- |\n"
    "| shfmt | `3.14.1` | `3.15.0` | |\n\n"
)
LOOKUP_ERRORS = "# Lookup errors\n\n- **shfmt**: RuntimeError: HTTP 503\n"
# What a run that did not complete leaves behind: a traceback on stderr and
# nothing at all on stdout.
TRACEBACK = "Traceback (most recent call last):\nRuntimeError: synthetic\n"


def run_block(name):
    """Read a named step's literal run block without a YAML dependency."""
    step = WORKFLOW.read_text().split(f"      - name: {name}\n", 1)[1]
    step = step.split("      - name:", 1)[0]
    lines = step.split("        run: |\n", 1)[1].splitlines()
    body = []
    for line in lines:
        if line and not line.startswith("          "):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body))


def install_audit(root, status, output, error):
    """Write a stand-in audit that prints fixed streams and exits a fixed status."""
    path = root / AUDIT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s' {shlex.quote(output)}\n"
        f"printf '%s' {shlex.quote(error)} >&2\n"
        f"exit {status}\n"
    )
    path.chmod(0o755)


def execute(status, output, error="", install=True):
    """Run the production block against one stand-in and collect everything it wrote."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = base / "workspace"
        runner_temp = base / "runner-temp"
        root.mkdir()
        runner_temp.mkdir()
        github_output = base / "github-output"
        github_output.write_text("")
        if install:
            install_audit(root, status, output, error)
        env = dict(
            os.environ,
            RUNNER_TEMP=str(runner_temp),
            GITHUB_OUTPUT=str(github_output),
        )
        # The runner's default `run:` shell is `bash -e {0}`. This workflow sets
        # neither `shell: bash` nor `defaults.run.shell`, so production has no
        # pipefail and no nounset and the block has to be correct without them.
        # tests/check-shell-discovery.py adds `-o pipefail` to a workflow that
        # likewise does not set it; do not copy that here.
        result = subprocess.run(
            ["bash", "-e", "-c", run_block(STEP)],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        report = runner_temp / "report.md"
        return {
            "code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "outputs": github_output.read_text(),
            "report": report.read_text() if report.exists() else None,
            "report_path": str(report),
        }


def context(label, run):
    return (
        f"{label}: exit {run['code']}\n"
        f"--- stdout ---\n{run['stdout']}"
        f"--- stderr ---\n{run['stderr']}"
        f"--- outputs ---\n{run['outputs']}"
    )


def expect_published(label, status, output):
    """A documented status with a usable report reaches the steps that act on it."""
    run = execute(status, output)
    assert run["code"] == 0, context(label, run)
    want = f"status={status}\nreport-path={run['report_path']}\n"
    assert run["outputs"] == want, context(label, run)
    # The downstream steps pass this file to `gh issue edit --body-file`, so the
    # report has to survive the step exactly as the audit wrote it.
    assert run["report"] == output, context(label, run)
    assert "::group::Report" in run["stdout"], context(label, run)
    print(f"{label}: published status={status}")


def expect_refused(label, message, **kwargs):
    """A run that did not complete fails the job and publishes nothing."""
    run = execute(**kwargs)
    assert run["code"] == 1, context(label, run)
    assert message in run["stderr"], context(label, run)
    # An empty GITHUB_OUTPUT is what keeps an unvalidated status away from the
    # `if:` conditions below the step, including any that later runs on failure.
    assert run["outputs"] == "", context(label, run)
    # Diagnostics come before the refusal, so a failing run still shows whatever
    # the audit managed to produce.
    assert "::group::Report" in run["stdout"], context(label, run)
    print(f"{label}: refused")


def main():
    # The three documented exits. Each has to keep working: the guards below
    # exist to reject everything else, not to narrow the contract.
    expect_published("current", 0, CURRENT)
    expect_published("outdated", 1, OUTDATED)
    expect_published("lookup errors", 2, LOOKUP_ERRORS)

    # The bug this file exists for. An unhandled exception, an unparseable PEP
    # 723 header and a uv that cannot resolve an interpreter all leave stdout
    # empty, and the old block handed that emptiness to `gh issue edit
    # --body-file`, erasing the tracking issue while the job reported green.
    empty_report = "with an empty report"
    expect_refused("crash on exit 1", empty_report, status=1, output="", error=TRACEBACK)
    # Status 2 has its own path out of the step, so the emptiness guard must not
    # be keyed to status 1 alone.
    expect_refused("crash on exit 2", empty_report, status=2, output="", error=TRACEBACK)

    # A status outside the contract, paired with a report that is not empty.
    # Nothing but the status guard can reject this one.
    expect_refused("unexpected status", "exited 3", status=3, output=OUTDATED)

    # No audit at the path at all, which is the shape of a uv that never ran the
    # script: the redirect still creates an empty report and bash returns 127.
    expect_refused(
        "missing audit", "exited 127", status=0, output="", install=False
    )


if __name__ == "__main__":
    main()
