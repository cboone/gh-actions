"""Exercise the real release auditor against permission and smoke defects."""

import argparse
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-module", type=Path, default=Path(__file__).with_name("audit-scrut-releases.py"))
    arguments = parser.parse_args()
    specification = importlib.util.spec_from_file_location("scrut_audit", arguments.audit_module)
    auditor = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(auditor)
    executable = shutil.which(os.environ.get("SCRUT_BIN", "scrut"))
    if executable is None:
        raise ValueError("Installed Scrut is required for release audit controls")
    data = Path(executable).read_bytes()
    host_os = {"Darwin": "macos", "Linux": "linux"}[platform.system()]
    host_arch = {"arm64": "aarch64", "aarch64": "aarch64", "x86_64": "x86_64"}[platform.machine()]

    with tempfile.TemporaryDirectory(prefix="scrut-audit-controls-") as temporary:
        cache = Path(temporary)

        def asset(name, mode):
            archive = cache / f"{name}.tar.gz"
            with tarfile.open(archive, "w:gz") as output:
                member = tarfile.TarInfo("scrut/scrut")
                member.size = len(data)
                member.mode = mode
                output.addfile(member, io.BytesIO(data))
            return {
                "name": archive.name,
                "version": "v0.4.3",
                "os": host_os,
                "arch": host_arch,
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            }

        valid = asset("valid", 0o755)
        result = auditor.audit(valid, cache, native_only=True)
        assert result["extracted_mode"] == "0o755", result
        assert result["execution"]["smoke_returncode"] == 0, result
        print("Valid executable archive: version and one snapshot case passed")

        def rejected(selected, diagnostic):
            try:
                auditor.audit(selected, cache, native_only=True)
            except ValueError as error:
                assert diagnostic in str(error), str(error)
            else:
                raise AssertionError(f"Auditor accepted defect: {diagnostic}")

        rejected(asset("non-executable", 0o644), "Non-executable archive member")
        print("Non-executable archive: rejected before binary invocation")

        real_run = subprocess.run
        for scenario in ["skipped-fence", "failed-assertion"]:
            measurement = {}

            def planted_run(command, *args, **kwargs):
                if len(command) > 1 and command[1] == "test":
                    spec = Path(command[2])
                    content = spec.read_text()
                    if scenario == "skipped-fence":
                        content = content.replace("```scrut", "```console")
                    else:
                        content = content.replace("\nscrut works\n```", "\nunexpected output\n```")
                    spec.write_text(content)
                    completed = real_run(command, *args, **kwargs)
                    measurement["returncode"] = completed.returncode
                    measurement["output"] = completed.stdout + completed.stderr
                    return completed
                return real_run(command, *args, **kwargs)

            with patch.object(auditor.subprocess, "run", side_effect=planted_run):
                rejected(valid, "Expected one executed, successful snapshot test")
            expected_exit = 0 if scenario == "skipped-fence" else 50
            assert measurement["returncode"] == expected_exit, measurement
            expected_count = "0 testcase(s)" if scenario == "skipped-fence" else "1 failed"
            assert expected_count in measurement["output"], measurement
            print(f"{scenario}: Scrut exit {expected_exit}; auditor rejected the defect")


if __name__ == "__main__":
    main()
