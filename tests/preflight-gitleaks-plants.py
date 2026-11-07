"""Load declared plant inputs and run unchanged baselines before a gate starts."""
# cspell:ignore functrace

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "2026-11-06-gitleaks-base-config-plants.json"


def run(argv, cwd, env):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, f"preflight command failed: {argv!r}\n{result.stdout}\n{result.stderr}"
    return {"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT / MANIFEST).read_text())
    assert isinstance(manifest, dict) and isinstance(manifest.get("inputs"), list)
    declarations = manifest["variants"] + manifest["controls"]
    assert declarations
    files = {name: ROOT / name for name in manifest["inputs"]}
    inputs = {}
    for name, path in files.items():
        assert not path.is_symlink() and path.is_file(), f"missing regular plant input: {name}"
        inputs[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": stat.S_IMODE(path.stat().st_mode)}
        if path.suffix in {".py", ".sh", ".mjs"}:
            text = path.read_text()
            assert not any(word in text for word in ["DEBUG", "BASH_COMMAND", "functrace", "set -T"]), f"fixture instrumentation: {name}"
        if path.suffix == ".sh":
            assert not re.search(r"(?m)^\s*(?:source|\.)\s", path.read_text()), f"declare and load the sourced library: {name}"
    for variant in manifest["variants"]:
        red = variant["red"]
        assert red["exit_code"] == 1 and "excludes" not in red
        assert len([x for x in red["contains"] if x.startswith("GITLEAKS_VERDICT assertion: ") and x.endswith("\n")]) == 1
    assert "excludes" not in manifest["green"] and "GITLEAKS_VERDICT green\n" in manifest["green"]["contains"]

    source = files["tests/check-gitleaks-base-config.mjs"].read_text()
    findings = files["tests/fixtures/gitleaks-findings.mjs"].read_text()
    assert "parseFindings(probe.stdout).filter(" in source and "JSON.parse(probe.stdout).filter(" not in source
    for required in ["Array.isArray(findings)", 'typeof finding.File === "string"', 'typeof finding.Fingerprint === "string"']:
        assert required in findings, f"missing fingerprint artifact guard: {required}"
    assert source.index('assert.ok(existsSync(join(source, ".gitleaksignore"))') < source.index('assert.equal(readFileSync(')
    verdict = files["tests/fixtures/gitleaks-assertion-verdict.mjs"].read_text()
    assert "error instanceof AssertionError" in verdict
    assert not any(word in source for word in ["mock(", "MagicMock", "createStub"]), "audit a new test double before plant execution"

    env = dict(os.environ, GITLEAKS_TEST_NODE_MODULES=str(ROOT / "node_modules"), PYTHONDONTWRITEBYTECODE="1", UV_PYTHON_DOWNLOADS="never")
    records = []
    for declaration in declarations:
        with tempfile.TemporaryDirectory(prefix="gitleaks-load-preflight-") as temporary:
            copy = Path(temporary)
            for name, path in files.items():
                destination = copy / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
            setup = run(["bash", "-euo", "pipefail", manifest["setup"]], copy, env)
            # The only Python subject modules load standard-library imports;
            # the verdict adapter loads the error fixture through runpy.
            loads = run(["uv", "run", "--no-project", "python", "-c", "import runpy; runpy.run_path('scripts/prepare-gitleaks-config.py', run_name='preflight'); runpy.run_path('tests/check-gitleaks-config-errors.py', run_name='preflight')"], copy, env)
            node_loads = run(["node", "--input-type=module", "-e", "await import('./tests/fixtures/workflow-steps.mjs'); await import('./tests/fixtures/gitleaks-findings.mjs'); await import('./tests/fixtures/gitleaks-assertion-verdict.mjs');"], copy, env)
            baseline = run(["bash", "-euo", "pipefail", manifest["check"]], copy, env)
            assert baseline["stdout"].endswith("GITLEAKS_VERDICT green\n"), "baseline did not produce its explicit green verdict"
            records.append({"name": declaration["name"], "setup": setup, "python_loads": loads, "node_loads": node_loads, "unchanged_baseline": baseline})
    args.output.write_text(json.dumps({"manifest": MANIFEST, "inputs": inputs, "records": records, "artifact_audit": "Fingerprint capture uses the shape-checked parser; ignore-file reads have existence checks and use the UTF-8 string contract. Verdict classification checks the exception type before reading its message.", "double_audit": "Git, gitleaks and uv are real binaries; malformed parser values are direct input cases, not tool doubles.", "data_only": [name for name in files if name.endswith(".patch")]}, indent=2) + "\n")
    print(str(args.output))


if __name__ == "__main__":
    main()
