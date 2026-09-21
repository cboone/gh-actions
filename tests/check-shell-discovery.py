#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Exercise lint-shell's actual run blocks with temporary tracked fixtures."""

# cspell:ignore cacheinfo

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
# everything else to the real binary. `${@+"$@"}` guards the empty argument
# list, which bash 3.2 rejects under `set -u` on macOS.
SHIMS = {
    # shfmt before 3.14.1 echoed back every explicitly supplied path in this
    # mode, non-shell files included. Selects the per-file fallback.
    "legacy": """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1-}" == '-f=0' ]]; then
  shift
  if [[ "${1-}" == '--' ]]; then
    shift
  fi
  printf '%s\\0' ${@+"$@"}
  exit 0
fi
exec "${REAL_SHFMT}" ${@+"$@"}
""",
    # An independent oracle for the fixed mode: classify one path at a time
    # with newline-mode -f, which filtered correctly before the fix, and
    # re-emit NUL-separated so a path holding a newline survives. Selects the
    # batched call.
    "modern": """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1-}" == '-f=0' ]]; then
  shift
  if [[ "${1-}" == '--' ]]; then
    shift
  fi
  for path in ${@+"$@"}; do
    if [[ -n "$("${REAL_SHFMT}" -f -- "${path}")" ]]; then
      printf '%s\\0' "${path}"
    fi
  done
  exit 0
fi
exec "${REAL_SHFMT}" ${@+"$@"}
""",
    # A release predating the flag refuses it rather than answering. Selects
    # the fallback through the probe's non-zero exit rather than its output,
    # which is the other half of that branch.
    "refusing": """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1-}" == '-f=0' ]]; then
  echo 'flag provided but not defined: -f=0' >&2
  exit 2
fi
exec "${REAL_SHFMT}" ${@+"$@"}
""",
}

# The notice the fallback branch prints, and the only way to tell from outside
# which branch ran.
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
    wrapper.write_text(SHIMS[label])
    wrapper.chmod(0o755)
    shimmed = env.copy()
    # Resolved from the unmodified PATH by the caller, so the wrapper cannot
    # find itself.
    shimmed["REAL_SHFMT"] = real
    shimmed["PATH"] = os.pathsep.join([str(directory), env["PATH"]])
    return shimmed


def manifest(runtime):
    """Decode the NUL-separated manifest the discovery step wrote."""
    paths = (runtime / "shell-scripts.txt").read_bytes().split(b"\0")
    assert paths[-1] == b"", paths
    return set(os.fsdecode(path) for path in paths[:-1])


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
        print("Empty tracked tree: notice and summary confirmed")

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
            # Equality, not containment: it is also what catches a RUNNER_TEMP
            # probe artifact reaching the manifest, since expected holds only
            # tracked paths.
            assert manifest(runtime) == expected, (label, shimmed)
            assert (SLOW_PATH_NOTICE in shimmed.stdout) == (label != "modern"), (
                label,
                shimmed.stdout,
            )
            assert Path(env["GITHUB_OUTPUT"]).read_text() == "found=true\n"
            assert not Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        print("Batched and per-file discovery agree, and only the fallback says so")

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
