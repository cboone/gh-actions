// Shared harness for fixtures that run a production workflow step. Reading the
// step out of the YAML keeps a fixture from drifting from what callers get, and
// keeping the spawn in one place keeps every fixture's shell identical to the
// runner's.
import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { parse } from "yaml";

export const repoRoot = new URL("../../", import.meta.url);
const workflowDir = new URL(".github/workflows/", repoRoot);

// GitHub runs `shell: bash` as `bash --noprofile --norc -e -o pipefail {0}`.
// There is deliberately no -u: adding it here would fail a step that the runner
// would have accepted.
export const RUNNER_BASH_ARGS = ["--noprofile", "--norc", "-e", "-o", "pipefail"];

export function loadWorkflow(name) {
  return parse(readFileSync(new URL(name, workflowDir), "utf8"));
}

export function stepOf(workflow, job, name) {
  const steps = (workflow.jobs[job]?.steps ?? []).filter((entry) => entry.name === name);
  assert.equal(steps.length, 1, `expected exactly one ${job}/${name} step, found ${steps.length}`);
  return steps[0];
}

// Run a step's script the way the runner would, and report what it did.
export function runStepScript(run, { cwd, env }) {
  const result = spawnSync("/bin/bash", [...RUNNER_BASH_ARGS, "-c", run], { cwd, env, encoding: "utf8" });
  assert.ifError(result.error);
  return {
    status: result.status,
    output: (result.stdout + result.stderr).replaceAll("::error::", "error: "),
  };
}

// GitHub accepts both extensions for a workflow, and a composite action's
// definition may use either. A walk that assumed one of them would let the
// other carry a `run:` block that no check ever reads.
const YAML_EXTENSIONS = [".yml", ".yaml"];

function isYaml(name) {
  return YAML_EXTENSIONS.some((extension) => name.endsWith(extension));
}

function* actionFiles(dir, prefix) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = new URL(`${entry.name}${entry.isDirectory() ? "/" : ""}`, dir);
    if (entry.isDirectory()) {
      yield* actionFiles(path, `${prefix}${entry.name}/`);
    } else if (entry.name === "action.yml" || entry.name === "action.yaml") {
      yield { path, label: `${prefix}${entry.name}` };
    }
  }
}

// Every `run:` block in the repository, keyed as `<file>::<job>::<step name>`.
// The job is part of the key because step names repeat across jobs: keying on
// the file and name alone would let one allowlist entry cover every same-named
// step in that file.
export function* runSteps() {
  for (const name of readdirSync(workflowDir).filter(isYaml)) {
    const doc = parse(readFileSync(new URL(name, workflowDir), "utf8"));
    for (const [jobId, job] of Object.entries(doc.jobs ?? {})) {
      for (const [index, step] of (job.steps ?? []).entries()) {
        if (typeof step.run === "string") {
          yield { key: `${name}::${jobId}::${step.name ?? `(unnamed step ${index})`}`, step };
        }
      }
    }
  }
  for (const { path, label } of actionFiles(new URL("actions/", repoRoot), "actions/")) {
    const doc = parse(readFileSync(path, "utf8"));
    for (const [index, step] of (doc.runs?.steps ?? []).entries()) {
      if (typeof step.run === "string") {
        yield { key: `${label}::runs::${step.name ?? `(unnamed step ${index})`}`, step };
      }
    }
  }
  for (const dir of [new URL(".github/actions/", repoRoot)]) {
    if (!existsSync(dir) || !statSync(dir).isDirectory()) continue;
    for (const { path, label } of actionFiles(dir, ".github/actions/")) {
      const doc = parse(readFileSync(path, "utf8"));
      for (const [index, step] of (doc.runs?.steps ?? []).entries()) {
        if (typeof step.run === "string") {
          yield { key: `${label}::runs::${step.name ?? `(unnamed step ${index})`}`, step };
        }
      }
    }
  }
}

// Assert that each entry in a documented exception set names exactly one real
// step, so an exception cannot outlive the step it was written for or silently
// widen to cover a second step that took the same name.
export function assertExactlyOne(entries, keys, description) {
  const counts = new Map();
  for (const key of keys) counts.set(key, (counts.get(key) ?? 0) + 1);
  const wrong = [...entries].filter((entry) => counts.get(entry) !== 1);
  assert.deepEqual(wrong, [], `${description} must each name exactly one step:\n  ${wrong.join("\n  ")}`);
}
