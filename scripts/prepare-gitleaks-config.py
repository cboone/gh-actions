#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Copy trusted gitleaks configuration and extensions outside the scan checkout."""

import argparse
import datetime
import json
from pathlib import Path
import sys
import tomllib


def checked_config(value):
    """Reject ambiguous keys without changing the trusted key names."""
    if isinstance(value, dict):
        result = {}
        seen = set()
        for key, item in value.items():
            folded = key.lower()
            if folded in seen:
                raise ValueError("Config contains duplicate case-insensitive keys")
            seen.add(folded)
            result[key] = checked_config(item)
        return result
    if isinstance(value, list):
        return [checked_config(item) for item in value]
    return value


def field_key(table, name):
    return next((key for key in table if key.lower() == name), None)


def quoted(value):
    return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")


def toml_value(value):
    """Emit inline TOML without changing parsed values or table nesting."""
    if isinstance(value, dict):
        return "{" + ", ".join(f"{quoted(key)} = {toml_value(item)}" for key, item in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, str):
        return quoted(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    raise ValueError("Unsupported TOML value")


def trusted_file(base, name):
    if Path(name).is_absolute():
        raise ValueError("gitleaks config must be relative to the base checkout")
    try:
        path = (base / name).resolve(strict=True)
    except FileNotFoundError:
        raise ValueError(f"Base file {name!r} is missing; config must be a file within the base checkout") from None
    if not path.is_relative_to(base) or not path.is_file():
        raise ValueError("gitleaks config must be a file within the base checkout")
    return path


def write_prepared(path, contents):
    try:
        if isinstance(contents, bytes):
            path.write_bytes(contents)
        else:
            path.write_text(contents, encoding="utf-8")
    except OSError as error:
        raise OSError(error.errno, f"Cannot write prepared file {path}: {error.strerror}") from None


def prepare(base, config, output):
    base = base.resolve(strict=True)
    output = output.resolve(strict=True)
    if output.is_relative_to(base):
        raise ValueError("Prepared files must be outside the base checkout")

    def copy_config(name, depth=0, ancestors=()):
        source = trusted_file(base, name)
        if source in ancestors or depth > 2:
            raise ValueError("Cyclic or over-depth config extension")
        try:
            with source.open("rb") as stream:
                data = checked_config(tomllib.load(stream))
        except ValueError as error:
            raise ValueError(f"Invalid TOML in {source.relative_to(base)}: {error}. Correct the base configuration") from None
        except OSError as error:
            raise OSError(error.errno, f"Cannot read base config {source}: {error.strerror}") from None
        extension_key = field_key(data, "extend")
        extension = data[extension_key] if extension_key is not None else {}
        if not isinstance(extension, dict):
            raise ValueError("Config extend must be a table")
        path_key = field_key(extension, "path")
        path = extension[path_key] if path_key is not None else ""
        if not isinstance(path, str):
            raise ValueError("Config extension path must be a string")
        if path:
            extension[path_key] = str(copy_config(path, depth + 1, (*ancestors, source)))
        destination = output / f"config-{depth}.toml"
        write_prepared(destination, "".join(f"{quoted(key)} = {toml_value(value)}\n" for key, value in data.items()))
        return destination

    default = base / ".gitleaks.toml"
    if config or default.exists() or default.is_symlink():
        copy_config(config or ".gitleaks.toml")
    else:
        write_prepared(output / "config-0.toml", "[extend]\nuseDefault = true\n")
    ignore = base / ".gitleaksignore"
    contents = trusted_file(base, ".gitleaksignore").read_bytes() if ignore.exists() or ignore.is_symlink() else b""
    write_prepared(output / ".gitleaksignore", contents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--config", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.base, args.config, args.output)
    except (ValueError, RuntimeError) as error:
        print("Invalid trusted gitleaks configuration: " + json.dumps(str(error)), file=sys.stderr)
        return 1
    except OSError as error:
        print("Gitleaks preparation I/O failure: " + json.dumps(str(error)) + ". Check the base checkout and runner temporary storage permissions/free space.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
