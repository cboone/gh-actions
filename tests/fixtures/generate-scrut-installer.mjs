import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { parse, stringify } from "yaml";

// Execute the public workflow's installer steps on the runner without its
// language build/test jobs. Fixture fetches use this checkout's reviewed SHA.
const language = process.argv[2];
assert.ok(["go", "zig"].includes(language), `Unknown workflow: ${language}`);
if (process.argv[3] === "--negative") {
  const helper = "actions/set-up-scrut/build-from-source.sh";
  const unsupported = spawnSync("bash", [helper], { env: { ...process.env, VERSION: "0.0.0" }, encoding: "utf8" });
  assert.equal(unsupported.status, 1, unsupported.stderr);
  assert.match(unsupported.stderr, /Unsupported scrut version/);
  const directory = mkdtempSync(join(tmpdir(), "scrut-negative-"));
  try {
    const source = readFileSync(helper, "utf8");
    const changed = source.replace(/local source_checksum="[a-f0-9]{64}"/, `local source_checksum="${"0".repeat(64)}"`);
    assert.notEqual(changed, source);
    const altered = join(directory, "build-from-source.sh");
    writeFileSync(altered, changed);
    const rejected = spawnSync("bash", [altered], { env: { ...process.env, VERSION: "0.4.3" }, encoding: "utf8" });
    assert.equal(rejected.status, 1, rejected.stderr);
    assert.match(rejected.stderr, /Scrut source archive checksum verification failed/);
  } finally {
    rmSync(directory, { recursive: true });
  }
  console.log("Scrut rejects unsupported versions and incorrect source checksums.");
  process.exit(0);
}
const workflow = parse(readFileSync(`.github/workflows/run-${language}-ci.yml`, "utf8"));
const names = ["Set up Rust for Scrut source build", "Build scrut from pinned source", "Install scrut"];
const steps = workflow.jobs.scrut.steps.filter((step) => names.includes(step.name));
assert.deepEqual(
  steps.map((step) => step.name),
  names,
);
for (const step of steps) {
  if (step.env?.REQ_REPO) {
    assert.equal(step.env.REQ_REPO, "${{ job.workflow_repository }}");
    assert.equal(step.env.REQ_SHA, "${{ job.workflow_sha }}");
    step.env.REQ_REPO = "${{ github.repository }}";
    step.env.REQ_SHA = "${{ github.sha }}";
    // These settings must be displaced by the source-build isolation boundary.
    step.env.CARGO_HOME = "${{ github.workspace }}/.local/consumer-cargo";
    step.env.RUSTFLAGS = "--invalid-scrut-fixture";
    step.env.RUSTC_WRAPPER = "/nonexistent-scrut-wrapper";
    step.env.CARGO_BUILD_TARGET = "invalid-scrut-target";
  }
}
steps.push({ name: "Verify installed Scrut executes", shell: "bash", run: "scrut --help > /dev/null" });
steps.push({ name: "Verify Scrut source rejection guards", shell: "bash", run: `node tests/fixtures/generate-scrut-installer.mjs ${language} --negative` });
const directory = ".local/scrut-installer";
mkdirSync(directory, { recursive: true });
mkdirSync(".local/consumer-cargo", { recursive: true });
writeFileSync(".local/consumer-cargo/config.toml", '[build]\nrustc-wrapper = "/nonexistent-cargo-config-wrapper"\n');
writeFileSync(
  `${directory}/action.yml`,
  stringify({
    name: "Scrut workflow installer fixture",
    description: "Execute the public Go or Zig workflow's Scrut installation steps.",
    runs: { using: "composite", steps },
  }),
);
