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
CHECKER = ROOT / "actions/run-trufflehog/check-allowlist.sh"

ALLOWLIST_MARKER = "gh-actions-allowlist-control-3f7d21c8b4"
# TruffleHog refuses to dial local addresses, so a URI carrying credentials
# and pointing at the loopback address cannot be verified, and is reported as
# an indeterminate result: the one class an allowlist entry may cover. Port 1
# can host no service either, so the outcome never depends on the runner.
#
# The URI is assembled here rather than written out as a literal. A literal
# would be a finding in this repository's own history, and this repository
# scans itself, which is the same reason the fixture that prompted #123 is
# now built at runtime in the project it came from.
FIXTURE_URI = "%s://%s:%s@%s/fixture" % (
    "https",
    "gh-actions",
    ALLOWLIST_MARKER,
    "127.0.0.1:1",
)
FIXTURE_CONTENT = f"# reviewed synthetic fixture\n{FIXTURE_URI}\n"
FIXTURE_PATH = "sample.txt"
FIXTURE_LINE = 2
# Names of the fields that carry credential material. The report must never
# print their values, and has no reason to print their names either.
SECRET_FIELDS = ("Raw", "RawV2", "Redacted", "StructuredData", "ExtraData")


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


def scan_step(path, step_name="Run trufflehog"):
    """Read the literal Bash block of the named step without YAML dependencies."""
    content = path.read_text()
    step = re.search(
        rf"(?m)^( *)- name: {re.escape(step_name)}\n(?P<body>(?:\1  .*\n|\n)+)",
        content,
    )
    if step is None:
        raise AssertionError(f"Missing {step_name} step in {path}")
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


def run_scan(script, directory, env, expected, label, found="Found verified result"):
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
    if expected == 183 and found not in result.stdout:
        raise AssertionError(f"{label}: no '{found}' in {result.stdout}")
    if expected == 0 and "Found verified result" in result.stdout:
        raise AssertionError(f"{label}: clean scan reported a finding")
    print(f"{label}: exit {expected}")
    return result


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
    return subprocess.check_output(
        ["git", "-C", str(directory), "rev-parse", "HEAD"], text=True
    ).strip()


def capture_findings(wrapper_dir, directory, destination):
    """Record one scan's JSON findings exactly as the checker will read them."""
    env = {
        **os.environ,
        "PATH": f"{wrapper_dir}{os.pathsep}{os.environ['PATH']}",
    }
    result = subprocess.run(
        [
            "trufflehog",
            "git",
            "file://.",
            "--no-update",
            "--results=verified,unknown",
            "--fail",
            "--json",
        ],
        cwd=directory,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=90,
    )
    if result.returncode != 183:
        raise AssertionError(
            f"expected a finding, got exit {result.returncode}\n{result.stderr}"
        )
    destination.write_text(result.stdout)
    findings = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(findings) != 1:
        raise AssertionError(f"expected exactly one finding, got {len(findings)}")
    return findings[0]


def entry_for(finding, reason="Reviewed synthetic fixture"):
    """Build the allowlist entry for the tuple TruffleHog actually emitted."""
    git = finding["SourceMetadata"]["Data"]["Git"]
    return {
        "reason": reason,
        "detector": finding["DetectorName"],
        "commit": git["commit"],
        "path": git["file"],
        "line": git["line"],
    }


def write_allowlist(path, document):
    path.write_text(json.dumps(document))
    return path


def check_report(output, label):
    """Assert a report named no secret, by value or by field name."""
    for marker in (MARKER, ALLOWLIST_MARKER):
        if marker in output:
            raise AssertionError(f"{label}: the report printed a credential")
    for field in SECRET_FIELDS:
        if field in output:
            raise AssertionError(f"{label}: the report named the {field} field")


def run_checker(checker, findings, allowlist, expected, label):
    result = subprocess.run(
        [str(checker), "--findings", str(findings), "--allowlist", str(allowlist)],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    if result.returncode != expected:
        raise AssertionError(
            f"{label}: expected exit {expected}, got {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    output = result.stdout + result.stderr
    check_report(output, label)
    print(f"{label}: exit {expected}")
    return output


def check_matching(base, findings, entry):
    """The exact reviewed tuple is accepted, and every changed field is not."""
    exact = write_allowlist(
        base / "allow-exact.json", {"version": 1, "entries": [entry]}
    )
    output = run_checker(CHECKER, findings, exact, 0, "allowlist exact tuple")
    if "allowed: " not in output or entry["reason"] not in output:
        raise AssertionError(f"exact tuple was not reported as allowed\n{output}")

    for field, replacement in (
        ("commit", "0" * 40),
        ("path", "other/sample.txt"),
        ("line", entry["line"] + 1),
        ("detector", "AWS"),
    ):
        mutated = {**entry, field: replacement}
        path = write_allowlist(
            base / f"allow-wrong-{field}.json", {"version": 1, "entries": [mutated]}
        )
        output = run_checker(CHECKER, findings, path, 1, f"allowlist wrong {field}")
        for expected in ("detector=", "verified=", "commit=", "path=", "line="):
            if expected not in output:
                raise AssertionError(f"wrong {field}: report omitted {expected}")


def check_rejections(base, findings, entry):
    """A malformed allowlist is refused rather than applied loosely."""
    invalid = {
        "trailing-garbage": '{"version": 1, "entries": []} {"version": 1}',
        "not-json": "{ this is not json",
        "not-an-object": "[]",
        "unknown-document-key": json.dumps(
            {"version": 1, "entries": [entry], "extra": True}
        ),
        "wrong-version": json.dumps({"version": 2, "entries": [entry]}),
        "empty-entries": json.dumps({"version": 1, "entries": []}),
        "unknown-entry-key": json.dumps(
            {"version": 1, "entries": [{**entry, "note": "x"}]}
        ),
        "missing-reason": json.dumps(
            {
                "version": 1,
                "entries": [{k: v for k, v in entry.items() if k != "reason"}],
            }
        ),
        "empty-reason": json.dumps({"version": 1, "entries": [{**entry, "reason": ""}]}),
        "short-commit": json.dumps(
            {"version": 1, "entries": [{**entry, "commit": entry["commit"][:7]}]}
        ),
        "uppercase-commit": json.dumps(
            {"version": 1, "entries": [{**entry, "commit": entry["commit"].upper()}]}
        ),
        "absolute-path": json.dumps(
            {"version": 1, "entries": [{**entry, "path": "/etc/passwd"}]}
        ),
        "parent-path": json.dumps(
            {"version": 1, "entries": [{**entry, "path": "../outside.txt"}]}
        ),
        "zero-line": json.dumps({"version": 1, "entries": [{**entry, "line": 0}]}),
        "fractional-line": json.dumps(
            {"version": 1, "entries": [{**entry, "line": 1.5}]}
        ),
        "duplicate-entries": json.dumps({"version": 1, "entries": [entry, entry]}),
    }
    for name, body in invalid.items():
        path = base / f"allow-invalid-{name}.json"
        path.write_text(body)
        run_checker(CHECKER, findings, path, 2, f"allowlist rejects {name}")


def check_verified_never_allowlisted(base, wrapper_dir, planted):
    """A verified finding fails even when its exact tuple is listed."""
    findings = base / "verified-findings.json"
    finding = capture_findings(wrapper_dir, planted, findings)
    if not finding["Verified"]:
        raise AssertionError("the control finding did not verify")
    entry = entry_for(finding, reason="Listed, and still refused")
    path = write_allowlist(
        base / "allow-verified.json", {"version": 1, "entries": [entry]}
    )
    output = run_checker(CHECKER, findings, path, 1, "allowlist refuses verified")
    if "verified finding is never allowlisted" not in output:
        raise AssertionError(f"the refusal was not explained\n{output}")


def check_planted_defect(base, findings, entry):
    """Prove the field comparison is what makes a changed field fail."""
    defective_dir = base / "defective-checker"
    defective_dir.mkdir()
    for name in ("check-allowlist.sh", "check-allowlist.jq"):
        shutil.copy(CHECKER.parent / name, defective_dir / name)
    program = defective_dir / "check-allowlist.jq"
    source = program.read_text()
    patched = source.replace("  and .detector == $finding.detector;", ";")
    if patched == source:
        raise AssertionError("could not remove the detector comparison")
    program.write_text(patched)
    (defective_dir / "check-allowlist.sh").chmod(0o755)

    mutated = {**entry, "detector": "AWS"}
    path = write_allowlist(
        base / "allow-defect.json", {"version": 1, "entries": [mutated]}
    )
    try:
        run_checker(
            defective_dir / "check-allowlist.sh",
            findings,
            path,
            1,
            "defective checker",
        )
    except AssertionError as error:
        if "expected exit 1, got 0" not in str(error):
            raise
        print("allowlist: dropping the detector comparison detected")
    else:
        raise AssertionError("dropping the detector comparison went undetected")


def check_working_tree_never_matches(base, env, action, entry):
    """A filesystem finding has no commit, so a commit-keyed entry cannot cover it."""
    repo = base / "working-tree-repo"
    repo.mkdir()
    (repo / FIXTURE_PATH).write_text(FIXTURE_CONTENT)
    # Same detector, path and line as the git fixture, so only the absent
    # commit can be what stops it matching.
    allowlist = write_allowlist(
        base / "allow-working-tree.json", {"version": 1, "entries": [entry]}
    )
    label = "allowlist never covers a working-tree finding"
    result = run_scan(
        action,
        repo,
        {
            **env,
            "SCAN_SCOPE": "working-tree",
            "TRUFFLEHOG_ARGS": "filesystem\n--directory\n.",
            "TRUFFLEHOG_ALLOWLIST": str(allowlist),
            "ALLOWLIST_CHECKER": str(CHECKER),
        },
        1,
        label,
    )
    output = result.stdout + result.stderr
    check_report(output, label)
    if "commit=none" not in output:
        raise AssertionError(f"{label}: the report did not show a missing commit")


def check_expected_findings(base, findings, entry):
    """A findings file the checker cannot read fails when results were reported."""
    empty = base / "empty-findings.json"
    empty.write_text("")
    allowlist = write_allowlist(
        base / "allow-expect.json", {"version": 1, "entries": [entry]}
    )
    run_checker(CHECKER, empty, allowlist, 0, "no findings reported, none seen")
    result = subprocess.run(
        [
            str(CHECKER),
            "--findings",
            str(empty),
            "--allowlist",
            str(allowlist),
            "--expect-findings",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )
    if result.returncode != 2:
        raise AssertionError(
            "findings reported but unreadable should exit 2, got "
            f"{result.returncode}\n{result.stdout}\n{result.stderr}"
        )
    if "none reached the allowlist checker" not in result.stderr:
        raise AssertionError(f"the disagreement was not explained\n{result.stderr}")
    print("allowlist refuses a scan whose findings it cannot read: exit 2")

    # A reason cannot write its own report lines, so it cannot forge a verdict.
    forged = write_allowlist(
        base / "allow-forged.json",
        {"version": 1, "entries": [{**entry, "reason": "reviewed\nblocked: forged"}]},
    )
    run_checker(CHECKER, findings, forged, 2, "allowlist rejects a forged reason")


def assert_no_injected_command(output, marker, label):
    """The planted text must never open a line.

    A line is a workflow command only when it starts with "::" after leading
    whitespace, so encoded text sitting inside a legitimate annotation is
    inert. Asserting the marker is absent altogether would fail on exactly
    the output that proves the encoding worked.
    """
    for line in output.splitlines():
        if line.strip().startswith(f"::error::{marker}"):
            raise AssertionError(
                f"{label}: a line opened with the planted command\n{output}"
            )


def check_no_command_injection(base, entry):
    """Nothing the allowlist carries can open a workflow command line."""
    empty = base / "no-findings.json"
    empty.write_text("")

    # The runner percent-decodes a workflow command's data, so an entry field
    # holding the text "%0A" would become a newline the schema never sees.
    percent = write_allowlist(
        base / "allow-percent.json",
        {
            "version": 1,
            "entries": [{**entry, "path": "fixture%0A::error::FORGED-DATA"}],
        },
    )
    output = run_checker(CHECKER, empty, percent, 0, "percent escapes cannot inject")
    if "%250A" not in output:
        raise AssertionError(f"the percent sign was not encoded\n{output}")
    assert_no_injected_command(output, "FORGED-DATA", "percent escapes")

    # A key name is not a value, so field validation never sees it, and it
    # reaches the log through jq's diagnostic rather than the report.
    injected = base / "allow-injected-key.json"
    injected.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [{**entry, "bad\n::error::FORGED-KEY": 1}],
            }
        )
    )
    output = run_checker(CHECKER, empty, injected, 2, "a key name cannot inject")
    assert_no_injected_command(output, "FORGED-KEY", "key name")


def check_step_annotation_escaping(env, action, repo):
    """The step's own annotations encode the caller input they repeat."""
    label = "action encodes an allowlist path in its annotation"
    result = run_scan(
        action,
        repo,
        {
            **env,
            "SCAN_SCOPE": "full-history",
            "TRUFFLEHOG_ARGS": "git\nfile://.",
            # Never a real file, so the step fails on the missing allowlist
            # before scanning, which is the annotation under test.
            "TRUFFLEHOG_ALLOWLIST": "missing.json\n::error::FORGED-PATH",
            "ALLOWLIST_CHECKER": str(CHECKER),
        },
        1,
        label,
    )
    output = result.stdout + result.stderr
    assert_no_injected_command(output, "FORGED-PATH", label)
    if "%0A" not in output:
        raise AssertionError(f"{label}: the newline was not encoded\n{output}")


def check_malformed_findings(base, findings, entry):
    """A finding the checker cannot read fails closed rather than matching."""
    allowlist = write_allowlist(
        base / "allow-malformed.json", {"version": 1, "entries": [entry]}
    )
    source = json.loads(findings.read_text().splitlines()[0])

    # Verified decides whether an entry may cover a finding at all, so a
    # missing or non-boolean value must not read as "not verified".
    for label, mutate in (
        ("missing Verified", lambda f: f.pop("Verified")),
        ("non-boolean Verified", lambda f: f.update({"Verified": "false"})),
        ("missing DetectorName", lambda f: f.pop("DetectorName")),
        ("non-string DetectorName", lambda f: f.update({"DetectorName": 17})),
    ):
        malformed = json.loads(json.dumps(source))
        mutate(malformed)
        path = base / f"findings-{label.replace(' ', '-')}.json"
        path.write_text(json.dumps(malformed) + "\n")
        run_checker(CHECKER, path, allowlist, 2, f"findings rejected: {label}")

    # The location fields are one source's tuple. Read field by field, a Git
    # commit could pair with a Filesystem path and line and match an entry
    # written for something else, so carrying both sources is refused.
    mixed = json.loads(json.dumps(source))
    mixed["SourceMetadata"]["Data"] = {
        "Git": {"commit": entry["commit"]},
        "Filesystem": {"file": entry["path"], "line": entry["line"]},
    }
    path = base / "findings-mixed-source.json"
    path.write_text(json.dumps(mixed) + "\n")
    run_checker(CHECKER, path, allowlist, 2, "findings rejected: mixed source")

    # Rendering calls tostring, so a location field of the wrong type would
    # dump whatever structure the scanner emitted into the report. Only the
    # type name may reach the diagnostic.
    for label, git in (
        ("object commit", {"commit": {"RawV2": ALLOWLIST_MARKER}, "file": "a", "line": 1}),
        ("array path", {"commit": "b" * 40, "file": [ALLOWLIST_MARKER], "line": 1}),
        ("string line", {"commit": "b" * 40, "file": "a", "line": ALLOWLIST_MARKER}),
    ):
        malformed = json.loads(json.dumps(source))
        malformed["SourceMetadata"]["Data"] = {"Git": git}
        path = base / f"findings-{label.replace(' ', '-')}.json"
        path.write_text(json.dumps(malformed) + "\n")
        # run_checker already asserts the marker never reaches the output.
        run_checker(CHECKER, path, allowlist, 2, f"findings rejected: {label}")

    # A git finding missing its path cannot borrow one, so it cannot match.
    partial = json.loads(json.dumps(source))
    partial["SourceMetadata"]["Data"] = {"Git": {"commit": entry["commit"]}}
    path = base / "findings-partial-git.json"
    path.write_text(json.dumps(partial) + "\n")
    output = run_checker(CHECKER, path, allowlist, 1, "partial git metadata blocks")
    if "path=none" not in output:
        raise AssertionError(f"the missing path was not reported\n{output}")

    # Git permits a newline in a filename, so a finding must not be able to
    # write its own report lines either.
    injected = json.loads(json.dumps(source))
    injected["SourceMetadata"]["Data"]["Git"]["file"] = "sample.txt\n::error::forged"
    path = base / "findings-injected-path.json"
    path.write_text(json.dumps(injected) + "\n")
    output = run_checker(CHECKER, path, allowlist, 1, "finding path cannot inject lines")
    # The runner reads a line as a workflow command only when it starts with
    # "::" after leading whitespace, so the escaped text staying inside a line
    # is the property that matters, not its absence from the report.
    assert_no_injected_command(output, "forged", "finding path")
    if "sample.txt\\n::error::forged" not in output:
        raise AssertionError(f"the newline was not rendered visibly\n{output}")


def check_action_output_flags(base, env, action, repo):
    """The action owns the output format the allowlist is matched against."""
    allowlist = base / "allow-exact.json"
    # The =value forms matter as much as the bare ones: --json-legacy=true
    # wins over the appended --json and leaves the findings file empty, which
    # a checker seeing no findings would otherwise read as a clean scan.
    for flag in (
        "--json-legacy",
        "--json-legacy=true",
        "--sarif",
        "--sarif=true",
        "--github-actions",
        "--github-actions=true",
    ):
        label = f"action rejects {flag} with an allowlist"
        result = run_scan(
            action,
            repo,
            {
                **env,
                "SCAN_SCOPE": "full-history",
                "TRUFFLEHOG_ARGS": f"git\nfile://.\n{flag}",
                "TRUFFLEHOG_ALLOWLIST": str(allowlist),
                "ALLOWLIST_CHECKER": str(CHECKER),
            },
            1,
            label,
        )
        if flag not in result.stdout + result.stderr:
            raise AssertionError(f"{label}: the refusal did not name the flag")

    # Without an allowlist there is nothing to match, so a caller's choice of
    # output format is left alone rather than quietly dropped.
    run_scan(
        action,
        repo,
        {
            **env,
            "SCAN_SCOPE": "full-history",
            "TRUFFLEHOG_ARGS": "git\nfile://.\n--json",
            "TRUFFLEHOG_ALLOWLIST": "",
        },
        183,
        "action keeps a caller's --json without an allowlist",
        found='"DetectorName":"URI"',
    )
    run_scan(
        action,
        repo,
        {
            **env,
            "SCAN_SCOPE": "full-history",
            "TRUFFLEHOG_ARGS": "git\nfile://.",
            "TRUFFLEHOG_ALLOWLIST": "",
        },
        183,
        "action reports as text without an allowlist",
        found="Found unverified result",
    )


def check_fetch_step_rejections(base):
    """The workflow's fetch step refuses what it cannot do, before scanning.

    Only CI reaches this step, because it needs the `job` context, so its
    guards are otherwise never executed. Running the literal block here covers
    them without a runner.
    """
    fetch = scan_step(
        ROOT / ".github/workflows/scan-for-secrets.yml", "Fetch allowlist checker"
    )
    allowlist = write_allowlist(
        base / "allow-fetch.json",
        {
            "version": 1,
            "entries": [
                {
                    "reason": "Fetch-step fixture",
                    "detector": "URI",
                    "commit": "c" * 40,
                    "path": "sample.txt",
                    "line": 1,
                }
            ],
        },
    )
    runner_temp = base / "fetch-runner-temp"
    runner_temp.mkdir()
    ready = {
        **os.environ,
        "REQ_REPO": "cboone/gh-actions",
        "REQ_SHA": "0" * 40,
        "TRUFFLEHOG_ALLOWLIST": str(allowlist),
        "RUNNER_TEMP": str(runner_temp),
    }

    # GitHub Enterprise Server populates neither value, and the step says so
    # rather than fetching from a URL it cannot build.
    for missing in ("REQ_REPO", "REQ_SHA"):
        result = run_scan(
            fetch,
            base,
            {**ready, missing: ""},
            1,
            f"fetch step rejects an empty {missing}",
        )
        if "Enterprise" not in result.stdout + result.stderr:
            raise AssertionError(f"{missing}: the GHES cause was not named")

    label = "fetch step rejects a missing allowlist file"
    result = run_scan(
        fetch,
        base,
        {**ready, "TRUFFLEHOG_ALLOWLIST": "no/such/allowlist.json"},
        1,
        label,
    )
    if "is not a file" not in result.stdout + result.stderr:
        raise AssertionError(f"{label}: the cause was not named")

    # jq is runner-provided, so its absence has to fail rather than skip. The
    # stub directory carries bash alone, since dropping that too would fail
    # the test for want of an interpreter rather than for want of jq.
    without_jq = base / "path-without-jq"
    without_jq.mkdir()
    (without_jq / "bash").symlink_to(shutil.which("bash"))
    label = "fetch step rejects a missing jq"
    result = run_scan(
        fetch,
        base,
        {**ready, "PATH": str(without_jq)},
        1,
        label,
    )
    if "jq is required" not in result.stdout + result.stderr:
        raise AssertionError(f"{label}: the cause was not named")


def check_allowlist(base, binary, custom_wrapper_dir, planted, action, workflow):
    """Cover the allowlist end to end, and through both entry points."""
    uri_dir = base / "bin-uri"
    uri_dir.mkdir()
    shim = uri_dir / "trufflehog"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        f"exec {shlex.quote(binary)} --include-detectors=URI \"$@\"\n"
    )
    shim.chmod(0o755)

    repo = base / "allowlist-repo"
    commit = sample_history(repo, FIXTURE_CONTENT)
    findings = base / "allowlist-findings.json"
    finding = capture_findings(uri_dir, repo, findings)
    if finding["Verified"]:
        raise AssertionError("the URI fixture verified; it must stay indeterminate")
    entry = entry_for(finding)
    expected = {
        "detector": "URI",
        "commit": commit,
        "path": FIXTURE_PATH,
        "line": FIXTURE_LINE,
    }
    for field, value in expected.items():
        if entry[field] != value:
            raise AssertionError(f"fixture {field} was {entry[field]}, not {value}")

    check_matching(base, findings, entry)
    check_rejections(base, findings, entry)
    check_expected_findings(base, findings, entry)
    check_malformed_findings(base, findings, entry)
    check_no_command_injection(base, entry)
    check_fetch_step_rejections(base)
    check_verified_never_allowlisted(base, custom_wrapper_dir, planted)
    check_planted_defect(base, findings, entry)

    empty = base / "no-findings.json"
    empty.write_text("")
    stale = write_allowlist(
        base / "allow-stale.json", {"version": 1, "entries": [entry]}
    )
    output = run_checker(CHECKER, empty, stale, 0, "allowlist stale entry")
    if "unused entry 0" not in output:
        raise AssertionError(f"a stale entry was not reported\n{output}")

    # Both entry points run the checker, on the scan they really perform.
    env = {**os.environ, "PATH": f"{uri_dir}{os.pathsep}{os.environ['PATH']}"}
    check_action_output_flags(base, env, action, repo)
    check_working_tree_never_matches(base, env, action, entry)
    check_step_annotation_escaping(env, action, repo)
    exact = base / "allow-exact.json"
    wrong = base / "allow-wrong-line.json"
    for name, script in (("action", action), ("workflow", workflow)):
        scan_env = {
            **env,
            "SCAN_SCOPE": "full-history",
            "TRUFFLEHOG_ARGS": "git\nfile://.",
            "ALLOWLIST_CHECKER": str(CHECKER),
        }
        label = f"{name} allowlist accepts the reviewed tuple"
        result = run_scan(
            script,
            repo,
            {**scan_env, "TRUFFLEHOG_ALLOWLIST": str(exact)},
            0,
            label,
        )
        output = result.stdout + result.stderr
        check_report(output, label)
        # Exit 0 alone would also be what a checker that reported nothing
        # returns, which is the shape a fail-open defect takes.
        if "allowed: " not in output or entry["reason"] not in output:
            raise AssertionError(f"{label}: the finding was not reported as allowed")
        label = f"{name} allowlist rejects a changed line"
        result = run_scan(
            script,
            repo,
            {**scan_env, "TRUFFLEHOG_ALLOWLIST": str(wrong)},
            1,
            label,
        )
        check_report(result.stdout + result.stderr, label)


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
                scan_env = {
                    **env,
                    "SCAN_SCOPE": scope,
                    "TRUFFLEHOG_ARGS": args,
                    # Empty means the enforced-flag path, unchanged by #123.
                    "TRUFFLEHOG_ALLOWLIST": "",
                }
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
            check_allowlist(base, binary, wrapper.parent, planted, action, workflow)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
