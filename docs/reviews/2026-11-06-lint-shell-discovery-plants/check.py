# cspell:ignore functrace
"""Run literal discovery fixtures after checking their reviewed shell forms."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import sys
import traceback

SOURCE = Path("tests/check-shell-discovery.py")
FOLDER = Path("docs/reviews/2026-11-06-lint-shell-discovery-plants")


def preflight():
    inventory = json.loads((FOLDER / "inventory.json").read_text())
    fixtures = {str(SOURCE), *(str(path) for path in FOLDER.glob("*.sh"))}
    assert set(inventory) == fixtures, "unlisted fixture paths"
    for name, digest in inventory.items():
        path = Path(name)
        assert path.is_file() and not path.is_symlink(), "missing regular fixture"
        raw = path.read_bytes()
        text = raw.decode()
        # Inspect whole files before checking hashes, so this backstop stands alone.
        forbidden = ("DEBUG", "BASH_COMMAND", "set -T", "functrace")
        assert not any(token in text for token in forbidden), "instrumented fixture"
        assert not any(tail and tail[0].isspace() for tail in text.split("trap")[1:]), "instrumented fixture"
        assert hashlib.sha256(raw).hexdigest() == digest, "unlisted fixture form"
    # Loading the fixture imports every dependency without running main.
    runpy.run_path(str(SOURCE), run_name="preflight")
    parsed = ast.parse(SOURCE.read_text())
    guarded_reads = {child for node in parsed.body
                     if isinstance(node, ast.FunctionDef) and node.name == "artifact"
                     for child in ast.walk(node)}
    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef) and node.name == "artifact":
            assert any(isinstance(child, ast.Assert) for child in node.body)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"read_text", "read_bytes"}:
                assert node in guarded_reads or ast.unparse(node.func.value) == "WORKFLOW", "unguarded artifact read"
    print("PREFLIGHT: imports and reviewed fixture contracts loaded")


def main():
    try:
        if "--preflight" in sys.argv:
            preflight()
        else:
            runpy.run_path(str(SOURCE), run_name="__main__")
            print("VERDICT: discovery fixtures green")
    except AssertionError as error:
        print(f"ASSERTION: {error}")
        frames = traceback.extract_tb(error.__traceback__)
        if frames:
            frame = frames[-1]
            print(f"{frame.filename}:{frame.lineno}: {frame.line}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
