#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check that trusted config failures identify their operation without exposing contents."""

from pathlib import Path
import subprocess
import sys
import tempfile


HELPER = Path(__file__).resolve().parents[1] / "scripts/prepare-gitleaks-config.py"


def main():
    with tempfile.TemporaryDirectory(prefix="gitleaks-config-errors-") as temporary:
        root = Path(temporary)
        base = root / "base"
        output = root / "output"
        base.mkdir()
        output.mkdir()
        config = base / ".gitleaks.toml"

        def run(destination=output):
            result = subprocess.run([sys.executable, str(HELPER), "--base", str(base), "--output", str(destination)], capture_output=True, text=True, check=False)
            assert result.returncode == 1, "invalid preparation must fail"
            assert "DO_NOT_PRINT_CONFIG_CONTENT" not in result.stderr, "diagnostic exposed config contents"
            return result.stderr

        config.write_text('[extend]\npath = "rules.toml"\n')
        (base / "rules.toml").write_text('marker = "DO_NOT_PRINT_CONFIG_CONTENT"\n[invalid')
        diagnostic = run()
        assert "Invalid TOML in rules.toml" in diagnostic, "malformed TOML diagnostic must identify the extended file"
        assert "Correct the base configuration" in diagnostic, "parse error must name a corrective action"
        print("malformed extended TOML: diagnostic identifies file and correction")

        (base / "rules.toml").unlink()
        diagnostic = run()
        assert "rules.toml" in diagnostic and "missing" in diagnostic, "missing extension diagnostic must identify the file"
        print("missing extension: diagnostic identifies file")

        config.unlink()
        invalid_output = root / "not-a-directory"
        invalid_output.write_text("owned fixture\n")
        diagnostic = run(invalid_output)
        assert "I/O failure" in diagnostic and "Cannot write prepared file" in diagnostic, "filesystem diagnostic must identify the failing operation"
        assert "storage permissions/free space" in diagnostic, "I/O error must name a corrective action"
        print("unusable output: diagnostic identifies I/O operation and correction")


if __name__ == "__main__":
    main()
