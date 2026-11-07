from pathlib import Path
import runpy


try:
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "check-gitleaks-config-errors.py"), run_name="__main__")
except AssertionError as error:
    if str(error) != "malformed TOML diagnostic must identify the extended file":
        raise
    print("GITLEAKS_VERDICT assertion: malformed TOML diagnostic must identify the extended file")
    raise SystemExit(1) from None
