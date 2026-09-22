import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { assertExactlyOne, loadWorkflow, runSteps, runStepScript, stepOf } from "./workflow-steps.mjs";

// The only expressions any `run:` block may interpolate, listed per step. All
// six are the documented shell-command inputs, which accept a whole command by
// design. The npm install ternaries that used to sit here are gone: both
// workflows now decide between `npm ci` and `npm install` inside the step,
// reading the lockfile path and the caller's opt-in through `env:` (#137).
//
// Each step's expressions are named individually rather than the step being
// allowlisted wholesale, so adding an ordinary data input beside a sanctioned
// command input is still reported. Allowlisting the step alone would let one
// exemption cover every later expression added to it.
const INTERPOLATION_ALLOWLIST = new Map([
  ["deploy-to-pages.yml::build::Build site", ["inputs.build-command"]],
  ["run-go-ci.yml::scrut::Scrut test setup", ["inputs.scrut-setup-cmd"]],
  ["run-go-ci.yml::scrut::Build binary for scrut tests", ["inputs.scrut-build-cmd"]],
  ["run-scrut-tests.yml::scrut::Scrut test setup", ["inputs.scrut-setup-cmd"]],
  ["run-zig-ci.yml::scrut::Scrut test setup", ["inputs.scrut-setup-cmd"]],
  ["run-zig-ci.yml::scrut::Build binary for scrut tests", ["inputs.scrut-build-cmd"]],
]);

// Whitespace inside an expression is insignificant, and the npm ternaries span
// several lines, so compare on a single-spaced form.
const EXPRESSION = /\$\{\{([\s\S]*?)\}\}/g;

function expressionsIn(run) {
  return [...run.matchAll(EXPRESSION)].map(([, inner]) => inner.replace(/\s+/g, " ").trim());
}

// `create-gh-release` tokenizes a line the enclosing `while IFS= read -r line`
// loop already split, so that line cannot contain a newline and needs no guard.
const NEWLINE_GUARD_EXEMPT = new Set(["actions/create-gh-release/action.yml::runs::Create GitHub Release"]);

// Any `read` that fills an array from a here-string, however it is spelled:
// `read -r -a x`, `read -ra x`, `IFS=" " read -a x`, braced or bare variable.
// Keying off one exact spelling would let an equivalent rewrite drop the guard
// requirement, which is the whole protection for the sites no scenario runs.
const ARRAY_READ = /\bread\b[^\n|;]*?-[A-Za-z]*a[A-Za-z]*\s+(\w+)[^\n|;]*<<<\s*"?\$\{?(\w+)\}?"?/g;

function newlineGuardFor(variable) {
  return `[[ "\${${variable}}" == *$'\\n'* ]]`;
}

const goCi = loadWorkflow("run-go-ci.yml");
const rustCi = loadWorkflow("run-rust-ci.yml");
const goRelease = loadWorkflow("release-go-binaries.yml");
const coverageStep = stepOf(goCi, "test", "Run tests with coverage");
const goreleaserStep = stepOf(goRelease, "release", "Run GoReleaser");
const goUploadStep = stepOf(goCi, "test", "Upload coverage to Codecov");
const rustUploadStep = stepOf(rustCi, "test", "Upload coverage to Codecov");

// Defaults come from the workflows so the scenarios cannot drift from what
// callers actually get.
const defaultTestFlags = goCi.on.workflow_call.inputs["test-flags"].default;
const defaultCodecovFile = goCi.on.workflow_call.inputs["codecov-files"].default;
const defaultGoreleaserArgs = goRelease.on.workflow_call.inputs["goreleaser-args"].default;

const root = mkdtempSync(join(tmpdir(), "workflow-arg-binding-"));
const binDir = join(root, "bin");
const argvFile = join(root, "argv.txt");

// Each stub records the argument vector it was handed, one element per line,
// which is the only way to see argument boundaries from outside the process.
function installStub(name) {
  const path = join(binDir, name);
  writeFileSync(path, ["#!/bin/sh", ': > "${ARGV_FILE}"', 'for arg in "$@"; do', '  printf \'%s\\n\' "${arg}" >> "${ARGV_FILE}"', "done", ""].join("\n"));
  chmodSync(path, 0o755);
}

function runStep(step, env) {
  rmSync(argvFile, { force: true });
  const result = runStepScript(step.run, {
    cwd: root,
    env: { ...process.env, ...env, PATH: `${binDir}:${process.env.PATH}`, ARGV_FILE: argvFile },
  });
  const argv = existsSync(argvFile) ? readFileSync(argvFile, "utf8").split("\n").slice(0, -1) : null;
  return { ...result, argv };
}

function goTest({ flags = defaultTestFlags, file = defaultCodecovFile } = {}) {
  return runStep(coverageStep, { TEST_FLAGS: flags, CODECOV_FILE: file });
}

function goreleaser(args = defaultGoreleaserArgs) {
  return runStep(goreleaserStep, { GORELEASER_ARGS: args });
}

function expectArgv(result, expected) {
  assert.equal(result.status, 0, result.output);
  assert.deepEqual(result.argv, expected, result.output);
}

function expectRejected(result, diagnostic) {
  assert.equal(result.status, 1, result.output);
  assert.ok(result.output.includes(diagnostic), result.output);
  assert.equal(result.argv, null, "the command ran despite a rejected input");
}

// No scenario may leave a side effect behind: that is what an input escaping
// into shell syntax would look like.
function expectNoSideEffects(...names) {
  for (const name of names) {
    assert.equal(existsSync(join(root, name)), false, `${name} was created, so the input reached the shell as source`);
  }
}

const scenarios = {
  // Every `run:` block is free of expressions except the documented interfaces,
  // checked expression by expression rather than step by step.
  policy() {
    const keys = [];
    const seen = new Map();
    const unexpected = [];
    for (const { key, step } of runSteps()) {
      keys.push(key);
      const expressions = expressionsIn(step.run);
      if (expressions.length === 0) continue;
      const allowed = INTERPOLATION_ALLOWLIST.get(key) ?? [];
      seen.set(key, expressions);
      for (const expression of expressions) {
        if (!allowed.includes(expression)) unexpected.push(`${key}: \${{ ${expression} }}`);
      }
    }
    assert.deepEqual(unexpected, [], `run: blocks interpolating an expression outside the allowlist:\n  ${unexpected.join("\n  ")}`);
    const stale = [];
    for (const [key, allowed] of INTERPOLATION_ALLOWLIST) {
      const expressions = seen.get(key);
      if (!expressions) {
        stale.push(`${key} (interpolates nothing now)`);
        continue;
      }
      for (const expression of allowed) {
        if (!expressions.includes(expression)) stale.push(`${key}: \${{ ${expression} }}`);
      }
    }
    assert.deepEqual(stale, [], `allowlist entries no longer present, so the allowlist is too wide:\n  ${stale.join("\n  ")}`);
    assertExactlyOne([...INTERPOLATION_ALLOWLIST.keys()], keys, "allowlist entries");
  },

  // The migrated steps declare the bindings the shell code reads.
  bindings() {
    const expected = [
      [coverageStep, { TEST_FLAGS: "${{ inputs.test-flags }}", CODECOV_FILE: "${{ inputs.codecov-files }}" }],
      [goUploadStep, { CODECOV_FILE: "${{ inputs.codecov-files }}" }],
      [rustUploadStep, { CODECOV_FILE: "${{ inputs.codecov-files }}" }],
      [goreleaserStep, { GORELEASER_ARGS: "${{ inputs.goreleaser-args }}" }],
    ];
    for (const [step, bindings] of expected) {
      for (const [name, value] of Object.entries(bindings)) {
        assert.equal(step.env?.[name], value, `${step.name}: ${name}`);
      }
    }
    assert.equal(coverageStep.shell, "bash");
    assert.equal(goreleaserStep.shell, "bash");
    assert.ok(coverageStep.run.includes('"-coverprofile=${CODECOV_FILE}"'), "the coverage path must be quoted");
    assert.ok(goUploadStep.run.includes('--file "${CODECOV_FILE}"'));
    assert.ok(rustUploadStep.run.includes('--file "${CODECOV_FILE}"'));
  },

  // Splitting behaves the same everywhere, so no site silently drops a line.
  // Every split must also expand its array quoted; actionlint's shellcheck pass
  // reports SC2068/SC2206 when it does not, and this repeats the rule here so a
  // workflow that skipped that lint would still be caught.
  guards() {
    const missing = [];
    const unquoted = [];
    const keys = [];
    for (const { key, step } of runSteps()) {
      keys.push(key);
      if (NEWLINE_GUARD_EXEMPT.has(key)) continue;
      for (const [, array, variable] of step.run.matchAll(ARRAY_READ)) {
        if (!step.run.includes(newlineGuardFor(variable))) missing.push(`${key} (${variable})`);
        const bare = new RegExp(`(?<!")\\$\\{${array}\\[@\\]\\}(?!")`);
        if (bare.test(step.run)) unquoted.push(`${key} (${array})`);
      }
    }
    assert.deepEqual(missing, [], `read into an array without a newline guard:\n  ${missing.join("\n  ")}`);
    assert.deepEqual(unquoted, [], `array expanded unquoted, so it re-splits and globs:\n  ${unquoted.join("\n  ")}`);
    assertExactlyOne(NEWLINE_GUARD_EXEMPT, keys, "newline-guard exemptions");
  },

  // Each site the scenarios below cannot execute is still known to be guarded,
  // so a silent removal shows up as a missing site rather than a passing run.
  coverage() {
    const guarded = new Set();
    for (const { key, step } of runSteps()) {
      if (NEWLINE_GUARD_EXEMPT.has(key)) continue;
      for (const [, , variable] of step.run.matchAll(ARRAY_READ)) guarded.add(`${key} (${variable})`);
    }
    assert.deepEqual([...guarded].sort(), ["release-go-binaries.yml::release::Run GoReleaser (GORELEASER_ARGS)", "release-rust-binaries.yml::build::Build (BUILD_ARGS)", "release-zig-binaries.yml::release::Build and package (TARGETS)", "run-go-ci.yml::test::Run tests with coverage (TEST_FLAGS)", "run-rust-ci.yml::test::Install extra components (COMPONENTS)", "run-rust-ci.yml::test::Run tests (TEST_ARGS)", "run-rust-ci.yml::test::Run tests with coverage (TEST_ARGS)", "run-zig-ci.yml::cross-compile::Cross compile (TARGETS)", "run-zig-ci.yml::format::Check formatting (FMT_PATHS)", "run-rust-ci.yml::lint::Run clippy (CLIPPY_ARGS)"].sort(), "the set of guarded split sites changed; update this list and say why in docs/development.md");
  },

  defaults() {
    expectArgv(goTest(), ["test", "-v", "-race", "-coverprofile=coverage.out", "./..."]);
    expectArgv(goreleaser(), ["release", "--clean"]);
  },

  // A path with spaces stays one argument, which the interpolated form broke.
  spaces() {
    expectArgv(goTest({ file: "cover report.out" }), ["test", "-v", "-race", "-coverprofile=cover report.out", "./..."]);
    expectArgv(goreleaser("release --config my config.yml"), ["release", "--config", "my", "config.yml"]);
  },

  // Runs of spaces and tabs collapse; each flag stays its own argument.
  boundaries() {
    expectArgv(goTest({ flags: "-race   -count=1\t-v" }), ["test", "-v", "-race", "-count=1", "-v", "-coverprofile=coverage.out", "./..."]);
    expectArgv(goreleaser("  release \t --clean  "), ["release", "--clean"]);
  },

  // Shell metacharacters are data, not syntax.
  metacharacters() {
    expectArgv(goreleaser("release --clean; touch pwned"), ["release", "--clean;", "touch", "pwned"]);
    expectArgv(goreleaser("release && touch pwned2 | sh"), ["release", "&&", "touch", "pwned2", "|", "sh"]);
    expectArgv(goTest({ flags: "-race; touch pwned3" }), ["test", "-v", "-race;", "touch", "pwned3", "-coverprofile=coverage.out", "./..."]);
    expectArgv(goTest({ file: "coverage.out; touch pwned4" }), ["test", "-v", "-race", "-coverprofile=coverage.out; touch pwned4", "./..."]);
    expectNoSideEffects("pwned", "pwned2", "pwned3", "pwned4");
  },

  // Nothing in the value is expanded: no command substitution, no variables.
  substitution() {
    expectArgv(goreleaser("release $(touch pwned) `touch pwned2` ${HOME}"), ["release", "$(touch", "pwned)", "`touch", "pwned2`", "${HOME}"]);
    expectArgv(goTest({ file: "$(touch pwned3).out" }), ["test", "-v", "-race", "-coverprofile=$(touch pwned3).out", "./..."]);
    expectNoSideEffects("pwned", "pwned2", "pwned3");
  },

  // Documented behavior change: globs are passed through unexpanded.
  glob() {
    mkdirSync(join(root, "configs"), { recursive: true });
    writeFileSync(join(root, "configs/a.yml"), "");
    writeFileSync(join(root, "configs/b.yml"), "");
    expectArgv(goreleaser("release --config configs/*.yml"), ["release", "--config", "configs/*.yml"]);
    expectArgv(goTest({ flags: "-race *" }), ["test", "-v", "-race", "*", "-coverprofile=coverage.out", "./..."]);
  },

  // An empty value contributes no argument at all.
  empty() {
    expectArgv(goTest({ flags: "" }), ["test", "-v", "-coverprofile=coverage.out", "./..."]);
    expectArgv(goTest({ flags: "   " }), ["test", "-v", "-coverprofile=coverage.out", "./..."]);
    expectArgv(goreleaser(""), []);
  },

  // A multi-line value fails loudly instead of losing every line but the first.
  multiline() {
    expectRejected(goreleaser("release\n--clean"), "goreleaser-args must be a single line");
    expectRejected(goTest({ flags: "-race\n-count=1" }), "test-flags must be a single line");
  },
};

const name = process.argv[2];
const scenario = scenarios[name];
if (!scenario) throw new Error(`Unknown scenario: ${name}`);

try {
  mkdirSync(binDir, { recursive: true });
  installStub("go");
  installStub("goreleaser");
  scenario();
  console.log(`${name}: passed`);
} finally {
  rmSync(root, { recursive: true, force: true });
}
