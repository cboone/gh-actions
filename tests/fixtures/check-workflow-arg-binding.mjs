import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { parse } from "yaml";

// Read the production steps rather than duplicating their shell logic, then
// execute them the way a runner does: `shell: bash` is
// `bash --noprofile --norc -e -o pipefail`, without -u.
const repoRoot = new URL("../../", import.meta.url);
const workflowDir = new URL(".github/workflows/", repoRoot);
const actionsDir = new URL("actions/", repoRoot);

// The only `run:` blocks allowed to interpolate an expression. The first six
// are the documented shell-command inputs, which accept a whole command by
// design. The last two are ternaries whose branches are the string constants
// `npm ci` and `npm install`; no caller value reaches the shell.
const INTERPOLATION_ALLOWLIST = new Set(["deploy-to-pages.yml::Build site", "run-go-ci.yml::Scrut test setup", "run-go-ci.yml::Build binary for scrut tests", "run-scrut-tests.yml::Scrut test setup", "run-zig-ci.yml::Scrut test setup", "run-zig-ci.yml::Build binary for scrut tests", "deploy-to-pages.yml::Install npm dependencies", "publish-to-npm.yml::Install dependencies"]);

// `create-gh-release` tokenizes a line the enclosing `while IFS= read -r line`
// loop already split, so that line cannot contain a newline and needs no guard.
const NEWLINE_GUARD_EXEMPT = new Set(["actions/create-gh-release/action.yml::Create GitHub Release"]);

function loadWorkflow(name) {
  return parse(readFileSync(new URL(name, workflowDir), "utf8"));
}

function stepOf(workflow, job, name) {
  const step = workflow.jobs[job].steps.find((entry) => entry.name === name);
  assert.ok(step, `${job}/${name} not found`);
  return step;
}

// Every `run:` block in the repository, keyed as `<file>::<step name>`.
function* runSteps() {
  for (const file of readdirSync(workflowDir).filter((name) => name.endsWith(".yml"))) {
    const doc = parse(readFileSync(new URL(file, workflowDir), "utf8"));
    for (const job of Object.values(doc.jobs ?? {})) {
      for (const step of job.steps ?? []) {
        if (typeof step.run === "string") yield { key: `${file}::${step.name ?? "(unnamed)"}`, step };
      }
    }
  }
  for (const entry of readdirSync(actionsDir, { withFileTypes: true }).filter((item) => item.isDirectory())) {
    const path = new URL(`${entry.name}/action.yml`, actionsDir);
    if (!existsSync(path)) continue;
    const doc = parse(readFileSync(path, "utf8"));
    for (const step of doc.runs?.steps ?? []) {
      if (typeof step.run === "string") {
        yield { key: `actions/${entry.name}/action.yml::${step.name ?? "(unnamed)"}`, step };
      }
    }
  }
}

const goCi = loadWorkflow("run-go-ci.yml");
const rustCi = loadWorkflow("run-rust-ci.yml");
const goRelease = loadWorkflow("release-go-binaries.yml");
const coverageStep = stepOf(goCi, "test", "Run tests with coverage");
const goreleaserStep = stepOf(goRelease, "release", "Run GoReleaser");

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
  const result = spawnSync("/bin/bash", ["--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step.run], {
    cwd: root,
    env: { ...process.env, ...env, PATH: `${binDir}:${process.env.PATH}`, ARGV_FILE: argvFile },
    encoding: "utf8",
  });
  assert.ifError(result.error);
  const output = (result.stdout + result.stderr).replaceAll("::error::", "error: ");
  const argv = existsSync(argvFile) ? readFileSync(argvFile, "utf8").split("\n").slice(0, -1) : null;
  return { status: result.status, output, argv };
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
  // Every `run:` block is free of expressions except the documented interfaces.
  policy() {
    const found = [];
    for (const { key, step } of runSteps()) {
      if (step.run.includes("${{")) found.push(key);
    }
    const unexpected = found.filter((key) => !INTERPOLATION_ALLOWLIST.has(key));
    assert.deepEqual(unexpected, [], `run: blocks interpolating an expression outside the allowlist:\n  ${unexpected.join("\n  ")}`);
    const stale = [...INTERPOLATION_ALLOWLIST].filter((key) => !found.includes(key));
    assert.deepEqual(stale, [], `allowlist entries no longer interpolating, so the allowlist is too wide:\n  ${stale.join("\n  ")}`);
  },

  // The migrated steps declare the bindings the shell code reads.
  bindings() {
    const expected = [
      [coverageStep, { TEST_FLAGS: "${{ inputs.test-flags }}", CODECOV_FILE: "${{ inputs.codecov-files }}" }],
      [stepOf(goCi, "test", "Upload coverage to Codecov"), { CODECOV_FILE: "${{ inputs.codecov-files }}" }],
      [stepOf(rustCi, "test", "Upload coverage to Codecov"), { CODECOV_FILE: "${{ inputs.codecov-files }}" }],
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
    assert.ok(stepOf(goCi, "test", "Upload coverage to Codecov").run.includes('--file "${CODECOV_FILE}"'));
    assert.ok(stepOf(rustCi, "test", "Upload coverage to Codecov").run.includes('--file "${CODECOV_FILE}"'));
  },

  // Splitting behaves the same everywhere, so no site silently drops a line.
  guards() {
    const missing = [];
    for (const { key, step } of runSteps()) {
      if (NEWLINE_GUARD_EXEMPT.has(key)) continue;
      for (const [, variable] of step.run.matchAll(/read -r -a \w+ <<< "\$\{(\w+)\}"/g)) {
        if (!step.run.includes(`[[ "\${${variable}}" == *$'\\n'* ]]`)) missing.push(`${key} (${variable})`);
      }
    }
    assert.deepEqual(missing, [], `read -r -a without a newline guard:\n  ${missing.join("\n  ")}`);
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
