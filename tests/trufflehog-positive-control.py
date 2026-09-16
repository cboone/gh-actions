#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Exercise the actual TruffleHog scan steps with locally verified sample data."""

import http.server
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import textwrap
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "gh-actions-positive-control-7c926bf41a"


def action_version(path):
    """Read the action's quoted patch-version default without YAML dependencies."""
    inputs = path.read_text().split("\nruns:", 1)[0]
    version = re.search(
        r'(?m)^  version:\n(?:    .*\n)*?    default: "([0-9]+\.[0-9]+\.[0-9]+)"\n',
        inputs,
    )
    if version is None:
        raise AssertionError(f"Missing quoted patch-version default in {path}")
    return version[1]


def scan_step(path):
    """Read the literal Bash block of the named step without YAML dependencies."""
    content = path.read_text()
    step = re.search(
        r"(?m)^( *)- name: Run trufflehog\n(?P<body>(?:\1  .*\n|\n)+)",
        content,
    )
    if step is None:
        raise AssertionError(f"Missing Run trufflehog step in {path}")
    block = re.search(r"(?m)^ *run: \|\n((?: +.*\n|\n)+)", step["body"])
    if block is None:
        raise AssertionError(f"Expected literal run block in {path}")
    return textwrap.dedent(block[1])


class Verifier(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        matches = json.loads(body)
        valid = matches == {"PositiveControl": {"marker": [MARKER]}}
        self.send_response(200 if valid else 403)
        self.end_headers()
        self.wfile.write(b"synthetic marker")

    def log_message(self, *_args):
        pass


def run_scan(script, directory, env, expected, label):
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=directory,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=90,
    )
    if result.returncode != expected:
        raise AssertionError(
            f"{label}: expected exit {expected}, got {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    if expected == 183 and "Found verified result" not in result.stdout:
        raise AssertionError(f"{label}: no verified result in {result.stdout}")
    if expected == 0 and "Found verified result" in result.stdout:
        raise AssertionError(f"{label}: clean scan reported a finding")
    print(f"{label}: exit {expected}")


def sample_history(directory, content):
    """Import disposable fixture history, without changing the checkout."""
    subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
    data = content.encode()
    stream = (
        b"commit refs/heads/main\n"
        b"committer Sample <sample@example.invalid> 0 +0000\n"
        b"data 7\nsample\n\n"
        b"M 100644 inline sample.txt\n"
        + f"data {len(data)}\n".encode()
        + data
        + b"\n\n"
    )
    subprocess.run(
        ["git", "-C", str(directory), "fast-import", "--quiet"],
        input=stream,
        check=True,
        capture_output=True,
    )
    (directory / "sample.txt").write_text(content)
    subprocess.run(
        ["git", "-C", str(directory), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True,
    )
    subprocess.run(["git", "-C", str(directory), "read-tree", "HEAD"], check=True)


def main():
    binary = shutil.which("trufflehog")
    if binary is None:
        raise AssertionError("trufflehog must be installed")
    expected_version = action_version(ROOT / "actions/run-trufflehog/action.yml")
    version = subprocess.check_output([binary, "--version"], text=True).strip()
    if version != f"trufflehog {expected_version}":
        raise AssertionError(
            f"Expected pinned trufflehog {expected_version}, got {version}"
        )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Verifier)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="trufflehog-control-") as temp:
            base = Path(temp)
            config = base / "detector.json"
            config.write_text(
                json.dumps(
                    {
                        "detectors": [
                            {
                                "name": "PositiveControl",
                                "keywords": ["gh-actions-positive-control"],
                                "regex": {"marker": MARKER},
                                "verify": [
                                    {
                                        "endpoint": f"http://127.0.0.1:{server.server_port}",
                                        "unsafe": True,
                                    }
                                ],
                            }
                        ]
                    }
                )
            )
            wrapper = base / "bin" / "trufflehog"
            wrapper.parent.mkdir()
            wrapper.write_text(
                "#!/usr/bin/env bash\n"
                f"exec {shlex.quote(binary)} --config "
                f'{shlex.quote(str(config))} --include-detectors=CustomRegex "$@"\n'
            )
            wrapper.chmod(0o755)
            env = {
                **os.environ,
                "PATH": f"{wrapper.parent}{os.pathsep}{os.environ['PATH']}",
            }
            clean = base / "clean"
            planted = base / "planted"
            sample_history(clean, "ordinary sample data\n")
            sample_history(planted, MARKER + "\n")
            action = scan_step(ROOT / "actions/run-trufflehog/action.yml")
            workflow = scan_step(ROOT / ".github/workflows/scan-for-secrets.yml")
            for scope in ("working-tree", "full-history"):
                if scope == "full-history":
                    # The finding now exists only in history, not in sample.txt.
                    (planted / "sample.txt").unlink()
                args = (
                    "filesystem\n--directory\n."
                    if scope == "working-tree"
                    else "git\nfile://."
                )
                scan_env = {**env, "SCAN_SCOPE": scope, "TRUFFLEHOG_ARGS": args}
                for name, script in (("action", action), ("workflow", workflow)):
                    label = f"{name} {scope}"
                    run_scan(script, clean, scan_env, 0, label + " clean")
                    run_scan(script, planted, scan_env, 183, label + " finding")
                    if name == "action":
                        caller_env = {
                            **scan_env,
                            "TRUFFLEHOG_ARGS": args + "\n--no-update\n--fail",
                        }
                        run_scan(
                            script, clean, caller_env, 0, label + " caller flags clean"
                        )
                        run_scan(
                            script,
                            planted,
                            caller_env,
                            183,
                            label + " caller flags finding",
                        )
                    # Prove the assertion detects the precise defect in #111.
                    defective = script.replace(" --fail", "")
                    if defective == script:
                        raise AssertionError(f"{label}: missing --fail")
                    try:
                        run_scan(
                            defective, planted, scan_env, 183, label + " without --fail"
                        )
                    except AssertionError as error:
                        if "expected exit 183, got 0" not in str(error):
                            raise
                        print(f"{label}: removal of --fail detected")
                    else:
                        raise AssertionError(
                            f"{label}: removal of --fail went undetected"
                        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
