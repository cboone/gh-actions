import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { parse, stringify } from "yaml";

// Exercise the production Go/Zig installer and execution steps as composite
// actions. The language build jobs need consumer projects and are outside
// this installation fixture. Only workflow-specific context bindings change.
for (const language of ["go", "zig"]) {
  const workflow = parse(readFileSync(`.github/workflows/run-${language}-ci.yml`, "utf8"));
  const steps = workflow.jobs.scrut.steps;
  const names = ["Set up Rust for Scrut source build", "Build scrut from pinned source", "Install scrut", "Run scrut tests"];
  const selected = steps.filter((step) => names.includes(step.name)).map((step) => structuredClone(step));
  assert.deepEqual(
    selected.map((step) => step.name),
    names,
  );
  const build = selected[1];
  assert.equal(build.env.VERSION, "0.4.3");
  assert.equal(build.env.REQ_REPO, "${{ job.workflow_repository }}");
  assert.equal(build.env.REQ_SHA, "${{ job.workflow_sha }}");
  // This fixture belongs to Run CI's own checkout, so it fetches those same
  // files at the caller's SHA. The standalone workflow self-test separately
  // exercises the original job.workflow_* bindings through workflow_call.
  build.env.REQ_REPO = "${{ github.repository }}";
  build.env.REQ_SHA = "${{ github.sha }}";
  build.env.CARGO_HOME = "${{ github.workspace }}/.local/consumer-cargo";
  build.env.RUSTFLAGS = "--invalid-scrut-fixture";
  build.env.RUSTC_WRAPPER = "/nonexistent-scrut-wrapper";
  build.env.CARGO_BUILD_TARGET = "invalid-scrut-target";
  const run = selected[3];
  assert.equal(run.env.SCRUT_ENV, "${{ inputs.scrut-env }}");
  assert.equal(run.env.SCRUT_TEST_DIR, "${{ inputs.scrut-test-dir }}");
  run.env.SCRUT_ENV = "SCRUT_BIN=scrut";
  run.env.SCRUT_TEST_DIR = "tests/scrut/installation.md";
  run.shell = "bash";
  const directory = `.local/scrut-installers/${language}`;
  mkdirSync(directory, { recursive: true });
  writeFileSync(
    `${directory}/action.yml`,
    stringify({
      name: `Scrut ${language} installer fixture`,
      description: "Execute production installer and snapshot steps",
      runs: { using: "composite", steps: selected },
    }),
  );
}

mkdirSync(".local/consumer-cargo", { recursive: true });
writeFileSync(".local/consumer-cargo/config.toml", '[build]\nrustc-wrapper = "/nonexistent-cargo-config-wrapper"\n');
