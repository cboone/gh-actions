#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Fixture for the setup-uv scrut test.

A PEP 723 script that runs from its shebang alone, so executing it proves
that run-scrut-tests.yml put a working uv on PATH.
"""

print("hello from a PEP 723 script")
