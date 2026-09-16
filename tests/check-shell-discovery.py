#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Exercise lint-shell's actual run blocks with temporary tracked fixtures."""

# cspell:ignore cacheinfo

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/lint-shell.yml"


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
            "tools/posix": "#!/bin/sh\nprintf '%s\\n' hello\n",
        }
        for name, contents in scripts.items():
            write(root, name, contents)
        write(root, "README.txt", "Sample data\n")
        write(root, "tools/program", "#!/usr/bin/env python3\nprint('hello')\n")
        write(root, ".editorconfig", "root = true\n[*]\nindent_style = space\nindent_size = 2\n")
        subprocess.run(["git", "add", "--", "."], cwd=root, env=env, check=True)
        # These must remain invisible even though a directory walk finds them.
        write(root, "cmake/untracked", good)
        write(root, "node_modules/untracked.sh", good)
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
        paths = (runtime / "shell-scripts.txt").read_bytes().split(b"\0")
        assert paths[-1] == b""
        assert set(os.fsdecode(path) for path in paths[:-1]) == set(scripts), paths
        assert Path(env["GITHUB_OUTPUT"]).read_text() == "found=true\n"
        assert not Path(env["GITHUB_STEP_SUMMARY"]).read_text()
        print("Tracked discovery: nested shebangs, extensions and unusual paths confirmed")

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

        write(root, "tools/nested/path with spaces", "#!/usr/bin/env bash\nif true; then\n    echo hello\nfi\n")
        formatted = execute("Run shfmt check", root, env)
        assert formatted.returncode != 0, formatted
        write(root, "tools/nested/path with spaces", "#!/usr/bin/env bash\nif true; then\n  echo hello\nfi\n")
        formatted = execute("Run shfmt check", root, env)
        assert formatted.returncode == 0, formatted.stdout + formatted.stderr
        print("shfmt: extension-less formatting defect reported; EditorConfig style passes")


if __name__ == "__main__":
    main()
