import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { parse, stringify } from "yaml";

// Execute the public workflow's installer steps on the runner without its
// language build/test jobs. Fixture fetches use this checkout's reviewed SHA.
const language = process.argv[2];
assert.ok(["go", "zig"].includes(language), `Unknown workflow: ${language}`);
const workflow = parse(readFileSync(`.github/workflows/run-${language}-ci.yml`, "utf8"));
const names = ["Set up Rust for Linux arm64 source build", "Build scrut for Linux arm64", "Install scrut"];
const steps = workflow.jobs.scrut.steps.filter((step) => names.includes(step.name));
assert.deepEqual(
  steps.map((step) => step.name),
  names,
);
for (const step of steps) {
  if (step.env?.SOURCE_REPO) {
    assert.equal(step.env.SOURCE_REPO, "${{ job.workflow_repository }}");
    assert.equal(step.env.SOURCE_SHA, "${{ job.workflow_sha }}");
    step.env.SOURCE_REPO = "${{ github.repository }}";
    step.env.SOURCE_SHA = "${{ github.sha }}";
  }
}
steps.push({ name: "Verify installed Scrut executes", shell: "bash", run: "scrut --help > /dev/null" });
const directory = ".local/scrut-installer";
mkdirSync(directory, { recursive: true });
writeFileSync(
  `${directory}/action.yml`,
  stringify({
    name: "Scrut workflow installer fixture",
    description: "Execute the public Go or Zig workflow's Scrut installation steps.",
    runs: { using: "composite", steps },
  }),
);
