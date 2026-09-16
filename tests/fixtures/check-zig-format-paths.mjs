import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { parse } from "yaml";

// Read the production step and default rather than duplicating their shell logic.
const workflowPath = new URL("../../.github/workflows/run-zig-ci.yml", import.meta.url);
const workflow = parse(readFileSync(workflowPath, "utf8"));
const defaultPaths = workflow.on.workflow_call.inputs["fmt-paths"].default;
const step = workflow.jobs.format.steps.find((entry) => entry.name === "Check formatting");
assert.equal(step.shell, "bash");
assert.equal(step.env.FMT_PATHS, "${{ inputs.fmt-paths }}");

const scenario = process.argv[2];
const root = mkdtempSync(join(tmpdir(), "zig-format-paths-"));
const manifest = join(root, "build.zig.zon");
const unformattedManifest = '.{.name=.sample,.version="0.0.0",.paths=.{"src"}}\n';

function zig(...args) {
  const result = spawnSync("zig", args, { cwd: root, encoding: "utf8" });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stdout + result.stderr);
}

function check(paths, expectedStatus, diagnostic = "") {
  const result = spawnSync("/bin/bash", ["-euo", "pipefail", "-c", step.run], {
    cwd: root,
    env: { ...process.env, FMT_PATHS: paths },
    encoding: "utf8",
  });
  assert.ifError(result.error);
  const output = (result.stdout + result.stderr).replaceAll("::error::", "error: ");
  assert.equal(result.status, expectedStatus, output);
  assert.ok(output.includes(diagnostic), output);
}

try {
  mkdirSync(join(root, "src"));
  mkdirSync(join(root, "tools"));
  writeFileSync(join(root, "build.zig"), 'const std = @import("std");\n');
  writeFileSync(join(root, "src/main.zig"), "pub fn main() void {}\n");
  writeFileSync(join(root, "tools/helper.zig"), "pub fn helper() void {    }\n");
  writeFileSync(manifest, unformattedManifest);
  zig("fmt", "build.zig.zon");

  switch (scenario) {
    case "formatted-default":
      zig("fmt", "tools");
      check(defaultPaths, 0);
      break;
    case "default-excludes-tools":
      check(defaultPaths, 0);
      break;
    case "formatted-custom":
      zig("fmt", "tools");
      check(`${defaultPaths} tools`, 0);
      break;
    case "unformatted-custom":
      check(`${defaultPaths} tools`, 1, "tools/helper.zig");
      break;
    case "unformatted-manifest":
      writeFileSync(manifest, unformattedManifest);
      zig("fmt", "--check", "src/", "build.zig");
      check(defaultPaths, 1, "build.zig.zon");
      break;
    case "missing-manifest":
      rmSync(manifest);
      check(defaultPaths, 1, "build.zig.zon");
      break;
    case "without-manifest":
      rmSync(manifest);
      zig("fmt", "tools");
      check("build.zig src tools", 0);
      break;
    case "empty":
      check("", 1, "fmt-paths must contain at least one path");
      break;
    case "whitespace":
      check("   \t  ", 1, "fmt-paths must contain at least one path");
      break;
    default:
      throw new Error(`Unknown scenario: ${scenario}`);
  }
  console.log(`${scenario}: passed`);
} finally {
  rmSync(root, { recursive: true });
}
