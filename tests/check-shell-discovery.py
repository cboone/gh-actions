#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Exercise lint-shell's actual run blocks with temporary tracked fixtures."""

# cspell:ignore cacheinfo geteuid

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/lint-shell.yml"

# Discovery batches its `shfmt -f=0` call only when it measures the installed
# binary filtering a prose file out of that mode. Both answers have to be
# exercised wherever this runs, and the runner's own shfmt can only give one,
# so each branch is driven by a wrapper that intercepts -f=0 and delegates
# everything else to the real binary.
SHIMS = {
    # shfmt before 3.14.0 echoed back every explicitly supplied path in this
    # mode, non-shell files included. Selects the per-file fallback.
    "legacy": """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1-}" == '-f=0' ]]; then
  shift
  if [[ "${1-}" == '--' ]]; then
    shift
  fi
  printf '%s\\0' "$@"
  exit 0
fi
exec "${REAL_SHFMT}" "$@"
""",
    # An independent oracle for the fixed mode: classify one path at a time
    # with newline-mode -f, which filtered correctly before the fix, and
    # re-emit NUL-separated so a path holding a newline survives. Selects the
    # batched call. The oracle holds for regular-file arguments only, which is
    # what the workflow's -f/-L filter guarantees: real shfmt walks a
    # directory argument and emits what is inside, where this emits the
    # argument. Assigning before testing keeps shfmt's exit status, which a
    # command substitution inside `[[ ]]` would discard, so a file shfmt
    # cannot read fails here exactly as it fails the batched call.
    "modern": """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1-}" == '-f=0' ]]; then
  shift
  if [[ "${1-}" == '--' ]]; then
    shift
  fi
  for path in "$@"; do
    found="$("${REAL_SHFMT}" -f -- "${path}")" || exit "$?"
    if [[ -n "${found}" ]]; then
      printf '%s\\0' "${path}"
    fi
  done
  exit 0
fi
exec "${REAL_SHFMT}" "$@"
""",
    # shfmt added -f=0 in 3.11.0, so anything older refuses it rather than
    # answering. Selects the fallback through the probe's non-zero exit rather
    # than its output, which is the other half of that branch.
    "refusing": """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1-}" == '-f=0' ]]; then
  echo 'flag provided but not defined: -f=0' >&2
  exit 2
fi
exec "${REAL_SHFMT}" "$@"
""",
}

# Spliced into each wrapper in place of its `set` line, so every invocation
# leaves a byte behind and the process count becomes something to assert.
COUNT_CALL = 'set -euo pipefail\nprintf \'x\' >> "${SHFMT_CALL_LOG}"\n'

# The notice the fallback branch prints. It is the discriminator these cases
# use because the alternative, the `shell-candidate.txt` only the fallback
# writes, persists in the shared RUNNER_TEMP across runs.
SLOW_PATH_NOTICE = "discovery is checking one file at a time"


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


def execute(name, root, env):
    # RUNNER_TEMP and the two GitHub files are one location reused by every
    # call here, where a real job gets them fresh. Clear what the step may
    # read back or append to, so a case cannot pass on a neighbor's residue:
    # a stale probe answer would otherwise select the branch, and the step
    # appends to GITHUB_OUTPUT rather than overwriting it.
    runtime = Path(env["RUNNER_TEMP"])
    for stale in ("shfmt-find-probe.out", "shfmt-find-probe.err", "shell-candidate.txt"):
        (runtime / stale).unlink(missing_ok=True)
    for key in ("GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY", "SHFMT_CALL_LOG"):
        if key in env:
            Path(env[key]).write_text("")
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", run_block(name)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )


def write(root, name, contents):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)


def shimmed_env(base, env, label, real):
    """Put a `shfmt` wrapper ahead of the real binary on PATH."""
    directory = base / f"shim-{label}"
    directory.mkdir(exist_ok=True)
    wrapper = directory / "shfmt"
    # Every wrapper logs a byte per invocation, which is what lets this
    # check assert the process count the batched call exists to reduce.
    # Only calls through the wrapper count: the modern oracle reaches the real
    # binary directly, so its inner per-path calls are deliberately invisible.
    wrapper.write_text(SHIMS[label].replace("set -euo pipefail\n", COUNT_CALL, 1))
    wrapper.chmod(0o755)
    shimmed = env.copy()
    # Resolved from the unmodified PATH by the caller, so the wrapper cannot
    # find itself.
    shimmed["REAL_SHFMT"] = real
    shimmed["SHFMT_CALL_LOG"] = str(base / f"calls-{label}")
    shimmed["PATH"] = os.pathsep.join([str(directory), env["PATH"]])
    return shimmed


def manifest(runtime):
    """Decode the NUL-separated manifest the discovery step wrote."""
    paths = (runtime / "shell-scripts.txt").read_bytes().split(b"\0")
    assert paths[-1] == b"", paths
    return set(os.fsdecode(path) for path in paths[:-1])


def filtered_count(runtime):
    """How many tracked paths survived the step's -f/-L filter."""
    return (runtime / "discovery-input.txt").read_bytes().count(b"\0")


def call_count(env):
    """How many times the step invoked shfmt through the wrapper."""
    return len(Path(env["SHFMT_CALL_LOG"]).read_bytes())


def main():
    with tempfile.TemporaryDirectory(prefix="shell-discovery-") as directory:
        base = Path(directory)
        root = base / "checkout"
        root.mkdir()
        runtime = base / "runtime"
        runtime.mkdir()
        env = os.environ.copy()
        # Isolate the fixture from any enclosing Git repository or index.
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            env.pop(key, None)
        env.update(
            RUNNER_TEMP=str(runtime),
            GITHUB_OUTPUT=str(base / "output"),
            GITHUB_STEP_SUMMARY=str(base / "summary"),
        )
        subprocess.run(["git", "init", "--quiet"], cwd=root, env=env, check=True)

        empty = execute("Find shell scripts", root, env)
        assert empty.returncode == 0, empty.stderr
        assert "::notice::No tracked shell scripts found" in empty.stdout
        assert Path(env["GITHUB_OUTPUT"]).read_text() == "found=false\n"
        assert "checks were skipped" in Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        assert (runtime / "shell-scripts.txt").read_bytes() == b""
        # An empty tracked tree must not reach the probe at all, so it cannot
        # claim anything about the pinned shfmt. This is what the -s guard on
        # discovery-input.txt buys beyond skipping empty work.
        assert SLOW_PATH_NOTICE not in empty.stdout, empty.stdout
        print("Empty tracked tree: notice and summary confirmed, probe not reached")

        good = "#!/usr/bin/env bash\nprintf '%s\\n' hello\n"
        scripts = {
            "cmake/build-helper": good,
            "tools/nested/path with spaces": good,
            "tools/path\nwith newline": good,
            "ordinary.sh": "printf '%s\\n' hello\n",
            "ordinary.bash": good,
            "-leading-dash": good,
            "-": good,
            "tools/posix": "#!/bin/sh\nprintf '%s\\n' hello\n",
        }
        for name, contents in scripts.items():
            write(root, name, contents)
        write(root, "README.txt", "Sample data\n")
        write(root, "tools/program", "#!/usr/bin/env python3\nprint('hello')\n")
        write(root, ".editorconfig", "root = true\n[*]\nindent_style = space\nindent_size = 2\n")
        (root / "linked.sh").symlink_to("generated.sh")
        subprocess.run(["git", "add", "--", "."], cwd=root, env=env, check=True)
        # These must remain invisible even though a directory walk finds them.
        write(root, "cmake/untracked", good)
        write(root, "node_modules/untracked.sh", good)
        write(root, "generated.sh", good)
        # A submodule entry names a directory rather than files within it.
        subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo",
             "160000,0123456789012345678901234567890123456789,vendor/module"],
            cwd=root, env=env, check=True,
        )
        write(root, "vendor/module/untracked.sh", good)
        Path(env["GITHUB_OUTPUT"]).write_text("")
        Path(env["GITHUB_STEP_SUMMARY"]).write_text("")
        found = execute("Find shell scripts", root, env)
        assert found.returncode == 0, found.stderr
        expected = {"./-" if name == "-" else name for name in scripts}
        assert manifest(runtime) == expected, found
        assert Path(env["GITHUB_OUTPUT"]).read_text() == "found=true\n"
        assert not Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        print("Tracked discovery: nested shebangs, extensions and unusual paths confirmed")

        # Whichever branch the runner's own shfmt selected above, both must
        # produce that same manifest. Resolve the real binary before any shim
        # reaches PATH.
        real_shfmt = shutil.which("shfmt")
        assert real_shfmt, "shfmt must be installed to run this check"
        for label in SHIMS:
            probed = shimmed_env(base, env, label, real_shfmt)
            Path(env["GITHUB_OUTPUT"]).write_text("")
            Path(env["GITHUB_STEP_SUMMARY"]).write_text("")
            shimmed = execute("Find shell scripts", root, probed)
            assert shimmed.returncode == 0, shimmed.stderr
            # Equality, not containment. Containment would still hold if the
            # probe's output check were dropped and the legacy wrapper's
            # echo-back put README.txt and .editorconfig in the manifest.
            assert manifest(runtime) == expected, (label, shimmed)
            assert (SLOW_PATH_NOTICE in shimmed.stdout) == (label != "modern"), (
                label,
                shimmed.stdout,
            )
            # The point of the change, asserted rather than assumed: the
            # batched branch spends one call on the probe and one on the whole
            # set, while the fallback spends one per surviving tracked path.
            # Degrading the batched call back to a process per file, with
            # `xargs -n1` or otherwise, fails here and nowhere else.
            calls = call_count(probed)
            if label == "modern":
                assert calls == 2, (label, calls)
            else:
                assert calls == 1 + filtered_count(runtime), (label, calls)
            assert Path(env["GITHUB_OUTPUT"]).read_text() == "found=true\n"
            assert not Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        print("Batched and per-file discovery agree, and only the fallback says so")
        print("Process count: one batched call versus one per tracked path")

        # A tracked file shfmt cannot read must fail the step, not drop
        # silently out of the manifest and go unlinted behind a green job.
        # Both branches abort on it, and the modern oracle only reproduces
        # that because it keeps shfmt's exit status rather than testing its
        # output. Extension-less on purpose: shfmt settles a `.sh` name
        # without opening the file. Root defeats the permission bit, so skip
        # there rather than assert something untrue.
        if os.geteuid() != 0:
            unreadable = root / "cmake/build-helper"
            unreadable.chmod(0o000)
            try:
                denied = execute("Find shell scripts", root, env)
                assert denied.returncode != 0, denied
                for label in SHIMS:
                    probed = shimmed_env(base, env, label, real_shfmt)
                    denied = execute("Find shell scripts", root, probed)
                    assert denied.returncode != 0, (label, denied)
            finally:
                unreadable.chmod(0o644)
            print("Unreadable tracked file: every branch fails rather than skipping it")

        outside = base / "outside"
        outside.mkdir()
        failed = execute("Find shell scripts", outside, env)
        assert failed.returncode != 0, failed
        assert "::notice::" not in failed.stdout
        print("Git discovery failure: reports failure instead of an empty-set notice")

        # A non-shell-only index must also produce the empty-set signal.
        subprocess.run(["git", "read-tree", "--empty"], cwd=root, env=env, check=True)
        subprocess.run(["git", "add", "README.txt"], cwd=root, env=env, check=True)
        empty = execute("Find shell scripts", root, env)
        assert empty.returncode == 0, empty.stderr
        assert "::notice::No tracked shell scripts found" in empty.stdout
        # Here the filter passes a file through and discovery rejects it, so
        # both branches run and must still report the empty set.
        for label in SHIMS:
            probed = shimmed_env(base, env, label, real_shfmt)
            Path(env["GITHUB_OUTPUT"]).write_text("")
            empty = execute("Find shell scripts", root, probed)
            assert empty.returncode == 0, (label, empty.stderr)
            assert manifest(runtime) == set(), (label, empty)
            assert Path(env["GITHUB_OUTPUT"]).read_text() == "found=false\n"
        print("Non-shell-only index: both branches discover nothing")
        subprocess.run(["git", "add", "--", *scripts], cwd=root, env=env, check=True)
        found = execute("Find shell scripts", root, env)
        assert found.returncode == 0, found.stderr

        # Both checkers must consume the manifest and report real defects.
        # Supply an explicit shell directive for the extension-only fixture.
        write(root, "ordinary.sh", "# shellcheck shell=bash\nprintf '%s\\n' hello\n")
        write(root, "cmake/build-helper", "#!/usr/bin/env bash\nvalue=$1\necho $value\n")
        checked = execute("Run ShellCheck", root, env)
        assert checked.returncode != 0 and "SC2086" in checked.stdout, checked
        write(root, "cmake/build-helper", good)
        checked = execute("Run ShellCheck", root, env)
        assert checked.returncode == 0, checked.stdout + checked.stderr
        print("ShellCheck: extension-less defect reported; corrected set passes")

        write(root, "-", "#!/usr/bin/env bash\nvalue=$1\necho $value\n")
        checked = execute("Run ShellCheck", root, env)
        assert checked.returncode != 0 and "SC2086" in checked.stdout, checked
        write(root, "-", good)
        checked = execute("Run ShellCheck", root, env)
        assert checked.returncode == 0, checked.stdout + checked.stderr
        write(root, "-", "#!/usr/bin/env bash\nif true; then\n    echo hello\nfi\n")
        formatted = execute("Run shfmt check", root, env)
        assert formatted.returncode != 0, formatted
        write(root, "-", good)
        formatted = execute("Run shfmt check", root, env)
        assert formatted.returncode == 0, formatted.stdout + formatted.stderr
        print("Literal dash filename: both checkers report defects and accept corrections")

        write(root, "tools/nested/path with spaces", "#!/usr/bin/env bash\nif true; then\n    echo hello\nfi\n")
        formatted = execute("Run shfmt check", root, env)
        assert formatted.returncode != 0, formatted
        write(root, "tools/nested/path with spaces", "#!/usr/bin/env bash\nif true; then\n  echo hello\nfi\n")
        formatted = execute("Run shfmt check", root, env)
        assert formatted.returncode == 0, formatted.stdout + formatted.stderr
        print("shfmt: extension-less formatting defect reported; EditorConfig style passes")


if __name__ == "__main__":
    main()
