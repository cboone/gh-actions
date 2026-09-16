"""Audit reviewed Scrut archives without trusting their platform labels."""

# cspell:ignore IIQQQQQQ

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import struct
import subprocess
import tempfile


def command(arguments):
    return subprocess.check_output(arguments, text=True).strip()


def elf_dependencies(data):
    """Read ELF64 program headers and DT_NEEDED without executing the file."""
    if data[4:6] != b"\x02\x01":
        raise ValueError("Expected a little-endian ELF64 executable")
    offset = struct.unpack_from("<Q", data, 32)[0]
    size, count = struct.unpack_from("<HH", data, 54)
    segments = [struct.unpack_from("<IIQQQQQQ", data, offset + i * size) for i in range(count)]
    interpreter = None
    dynamic = []
    for kind, _, start, _, _, length, _, _ in segments:
        if kind == 3:
            interpreter = data[start : start + length].rstrip(b"\0").decode()
        elif kind == 2:
            for position in range(start, start + length, 16):
                tag, value = struct.unpack_from("<qQ", data, position)
                if tag == 0:
                    break
                dynamic.append((tag, value))
    names = []
    string_address = next((value for tag, value in dynamic if tag == 5), None)
    if string_address is not None:
        string_offset = next(
            start + string_address - address
            for kind, _, start, address, _, length, _, _ in segments
            if kind == 1 and address <= string_address < address + length
        )
        for tag, value in dynamic:
            if tag == 1:
                start = string_offset + value
                names.append(data[start : data.index(b"\0", start)].decode())
    return {
        "interpreter": interpreter,
        "needed": names,
        "glibc_versions": sorted(set(match.decode() for match in re.findall(rb"GLIBC_\d+\.\d+(?:\.\d+)?", data))),
    }


def inspect_binary(binary):
    data = binary.read_bytes()
    description = command(["file", "-b", str(binary)])
    if data.startswith(b"\x7fELF"):
        machine = struct.unpack_from("<H", data, 18)[0]
        architecture = {62: "x86_64", 183: "aarch64"}.get(machine, f"ELF-machine-{machine}")
        return "linux", architecture, description, elf_dependencies(data)
    if data[:4] == b"\xcf\xfa\xed\xfe":
        cpu = struct.unpack_from("<I", data, 4)[0]
        architecture = {0x1000007: "x86_64", 0x100000C: "aarch64"}.get(cpu, f"Mach-O-cpu-{cpu}")
        dependencies = {"status": "requires macOS otool"}
        if platform.system() == "Darwin":
            dependencies = {
                "needed": command(["otool", "-L", str(binary)]).splitlines()[1:],
                "build_versions": re.findall(
                    r"cmd LC_(?:BUILD_VERSION|VERSION_MIN_MACOSX)\n(?:.*\n){1,6}",
                    command(["otool", "-l", str(binary)]) + "\n",
                ),
            }
        return "macos", architecture, description, dependencies
    raise ValueError(f"Unsupported executable format: {description}")


def audit(asset, cache, native_only):
    host_os = {"Darwin": "macos", "Linux": "linux"}.get(platform.system())
    host_arch = {"arm64": "aarch64", "aarch64": "aarch64", "x86_64": "x86_64"}.get(platform.machine())
    if native_only and (asset["os"], asset["arch"]) != (host_os, host_arch):
        return None
    archive = cache / asset["name"]
    if not archive.exists():
        subprocess.run([
            "curl", "-sSfL", "--proto", "=https", "--proto-redir", "=https",
            "--retry", "3", "-o", str(archive), asset["url"],
        ], check=True)
    actual_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual_hash != asset["sha256"]:
        raise ValueError(f"Checksum mismatch for {asset['name']}: {actual_hash}")
    members = [member for member in command(["tar", "-tf", str(archive)]).splitlines() if member.split("/")[-1] == "scrut"]
    if len(members) != 1:
        raise ValueError(f"Expected exactly one scrut executable in {asset['name']}: {members}")
    with tempfile.TemporaryDirectory(dir=cache) as temporary:
        binary = Path(temporary) / "scrut"
        with binary.open("wb") as output:
            subprocess.run(["tar", "-xOf", str(archive), members[0]], stdout=output, check=True)
        binary.chmod(0o700)
        actual_os, actual_arch, description, dependencies = inspect_binary(binary)
        binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
        if "binary_sha256" in asset and binary_hash != asset["binary_sha256"]:
            raise ValueError(f"Executable checksum changed for {asset['name']}")
        result = {
            **asset,
            "binary_sha256": binary_hash,
            "actual_os": actual_os,
            "actual_arch": actual_arch,
            "format": description,
            "dependencies": dependencies,
            "execution": {"status": "not attempted on a different OS"},
        }
        if host_os == asset["os"]:
            execution = {"host_os": host_os, "host_arch": host_arch}
            try:
                version = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=30)
                execution.update(returncode=version.returncode, stdout=version.stdout.strip(), stderr=version.stderr.strip())
                if version.returncode == 0:
                    spec = Path(temporary) / "smoke.md"
                    spec.write_text('# Release smoke test\n\n```console\n$ printf "scrut works\\n"\nscrut works\n```\n')
                    smoke = subprocess.run([str(binary), "test", str(spec)], capture_output=True, text=True, timeout=30)
                    execution.update(smoke_returncode=smoke.returncode, smoke_stdout=smoke.stdout.strip(), smoke_stderr=smoke.stderr.strip())
            except OSError as error:
                execution.update(errno=error.errno, error=str(error))
            execution["status"] = "attempted"
            result["execution"] = execution
        if "actual_arch" in asset and (actual_os, actual_arch) != (asset["actual_os"], asset["actual_arch"]):
            raise ValueError(f"Executable format changed for reviewed asset {asset['name']}")
        if native_only and actual_os == host_os and actual_arch == host_arch:
            execution = result["execution"]
            if execution.get("returncode") != 0 or execution.get("smoke_returncode") != 0:
                raise ValueError(f"Native execution failed for {asset['name']}: {execution}")
        if native_only and actual_arch != host_arch:
            expected_errno = 8 if host_os == "linux" else 86
            if result["execution"].get("errno") != expected_errno:
                raise ValueError(f"Expected architecture rejection for incorrectly packaged {asset['name']}")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("tests/fixtures/scrut-release-assets.json"))
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-only", action="store_true")
    arguments = parser.parse_args()
    arguments.cache.mkdir(parents=True, exist_ok=True)
    results = []
    for asset in json.loads(arguments.manifest.read_text()):
        result = audit(asset, arguments.cache, arguments.native_only)
        if result is not None:
            results.append(result)
            print(f"{asset['name']}: {result['actual_os']} {result['actual_arch']}; {result['execution']['status']}")
    if not results:
        raise ValueError("No supported release assets selected for this host")
    arguments.output.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
