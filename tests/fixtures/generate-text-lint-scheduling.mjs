import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { parse, stringify } from "yaml";

// Copy production conditions into a runner-executed composite action. Tool
// commands become controlled exits; expected outcomes are specified separately.
const tools = ["markdownlint", "prettier", "cspell", "yamllint"];
const scenarios = {
  success: ["success", "success", "success", "success", "success"],
  "early-failure": ["success", "failure", "success", "success", "success"],
  "all-fail": ["success", "failure", "failure", "failure", "failure"],
  "setup-failure": ["skipped", "skipped", "skipped", "skipped", "skipped"],
  "disable-markdownlint": ["success", "skipped", "success", "success", "success"],
  "disable-prettier": ["success", "success", "skipped", "success", "success"],
  "disable-cspell": ["success", "success", "success", "skipped", "success"],
  "disable-yamllint": ["success", "success", "success", "success", "skipped"],
  "all-disabled": ["success", "skipped", "skipped", "skipped", "skipped"],
  "yamllint-only": ["success", "skipped", "skipped", "skipped", "success"],
};
const scenario = process.argv[2];
assert.ok(Object.hasOwn(scenarios, scenario), `Unknown scenario: ${scenario}`);
const workflow = parse(readFileSync(".github/workflows/lint-text.yml", "utf8"));
const sourceSteps = workflow.jobs["text-lint"].steps;
const readyIndex = sourceSteps.findIndex((step) => step.id === "lint-tools-ready");
assert.ok(readyIndex >= 0, "Missing setup-readiness step");
const checkNames = ["Run markdownlint", "Run Prettier check", "Run cspell", "Run yamllint"];
assert.deepEqual(
  sourceSteps.slice(readyIndex + 1).map((step) => step.name),
  checkNames,
  "All setup must precede readiness and all four lint checks",
);
assert.ok(
  sourceSteps.slice(0, readyIndex).some((step) => step.name === "Install yamllint with hash-pinned requirements"),
  "yamllint setup must precede readiness",
);

const inputs = {
  preset: "''",
  "use-consumer-versions": "false",
  "extra-cspell-packages": "''",
};
for (const tool of tools) {
  const enabled = scenario !== "all-disabled" && scenario !== `disable-${tool}` && (scenario !== "yamllint-only" || tool === "yamllint");
  inputs[`run-${tool}`] = String(enabled);
}
function bindInputs(condition) {
  return condition?.replace(/inputs\.([a-z-]+)/g, (_, input) => {
    assert.ok(Object.hasOwn(inputs, input), `Unhandled condition input: ${input}`);
    return inputs[input];
  });
}

const steps = sourceSteps.map((step, index) => {
  const checkIndex = checkNames.indexOf(step.name);
  const setupFails = scenario === "setup-failure" && step.name === "Install yamllint with hash-pinned requirements";
  const lintFails = checkIndex >= 0 && (scenario === "all-fail" || (scenario === "early-failure" && checkIndex === 0));
  return {
    name: step.name ?? `Setup ${index}`,
    id: step.id ?? (checkIndex >= 0 ? tools[checkIndex] : `setup-${index}`),
    ...(step.if === undefined ? {} : { if: bindInputs(step.if) }),
    ...(step["continue-on-error"] === undefined ? {} : { "continue-on-error": step["continue-on-error"] }),
    shell: "bash",
    run: index === readyIndex ? step.run : `exit ${setupFails || lintFails ? 1 : 0}`,
  };
});
steps.push({
  name: "Record scheduling outcomes",
  id: "report",
  if: "${{ !cancelled() }}",
  shell: "bash",
  env: {
    OUTCOMES: ["lint-tools-ready", ...tools].map((id) => `\${{ steps.${id}.outcome }}`).join(","),
    FAILED: "${{ failure() }}",
  },
  run: 'printf \'outcomes=%s\\nfailed=%s\\n\' "${OUTCOMES}" "${FAILED}" >> "${GITHUB_OUTPUT}"',
});
const action = {
  name: "Text lint scheduling fixture",
  description: "Exercise production step conditions on the GitHub runner.",
  outputs: {
    outcomes: { description: "Readiness and linter step outcomes.", value: "${{ steps.report.outputs.outcomes }}" },
    failed: { description: "Whether the composite accumulated a failure.", value: "${{ steps.report.outputs.failed }}" },
  },
  runs: { using: "composite", steps },
};
const directory = ".local/text-lint-scheduling";
mkdirSync(directory, { recursive: true });
writeFileSync(`${directory}/action.yml`, stringify(action));
const expectedFailure = ["early-failure", "all-fail", "setup-failure"].includes(scenario);
const expected = `expected-outcomes=${scenarios[scenario].join(",")}\nexpected-failed=${expectedFailure}\nexpected-outcome=${expectedFailure ? "failure" : "success"}\n`;
if (process.env.GITHUB_OUTPUT) {
  writeFileSync(process.env.GITHUB_OUTPUT, expected, { flag: "a" });
}
console.log(`${scenario}: ${scenarios[scenario].join(",")}; failure=${expectedFailure}`);
