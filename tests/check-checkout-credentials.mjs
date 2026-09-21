// Every `actions/checkout` step must say what it does with the job's Git
// credential, and only a step that pushes may keep it.
//
// `actions/checkout` writes the token it authenticated with into the
// checkout's `.git/config` and leaves it there for the rest of the job, where
// every later step can read it, including third-party tooling this repository
// invokes but does not control, and anything that archives or uploads the
// workspace. zizmor calls that `artipacked`. The default is the unsafe one, so
// a new checkout reintroduces the exposure by saying nothing at all; this
// check is what turns that silence red (#133).
//
// What it catches, because each makes the run fail: a checkout added without
// `persist-credentials`, a checkout that sets it to `true` without being
// listed below, and an entry below that no longer names a real step.
import assert from "node:assert/strict";
import { assertExactlyOne, usesSteps } from "./fixtures/workflow-steps.mjs";

// The complete set of checkouts allowed to keep their credential, each with
// the step that consumes it. Entries are named individually rather than whole
// files being exempted, so a second checkout added to one of these jobs is
// still reported.
const PERSISTS_CREDENTIALS = new Map([["release-rust-binaries.yml::homebrew::Check out the Homebrew tap", "the Commit and push formula step pushes to the tap with it"]]);

const CHECKOUT = /^actions\/checkout@/;

const keys = [];
const missing = [];
const unexpected = [];

for (const { key, step } of usesSteps()) {
  keys.push(key);
  if (!CHECKOUT.test(step.uses)) continue;

  const value = step.with?.["persist-credentials"];
  if (value === undefined) {
    missing.push(key);
  } else if (value === true && !PERSISTS_CREDENTIALS.has(key)) {
    unexpected.push(key);
  } else if (value !== true && value !== false) {
    // A quoted "false" is truthy to the action, so it would persist the
    // credential while reading as if it did not.
    unexpected.push(`${key} (persist-credentials: ${JSON.stringify(value)} is not a boolean)`);
  } else if (value === false && PERSISTS_CREDENTIALS.has(key)) {
    unexpected.push(`${key} (listed as persisting its credential, but sets false)`);
  }
}

assert.deepEqual(missing, [], `actions/checkout steps that do not set persist-credentials:\n  ${missing.join("\n  ")}`);
assert.deepEqual(unexpected, [], `actions/checkout steps whose persist-credentials value is not allowed:\n  ${unexpected.join("\n  ")}`);
assertExactlyOne([...PERSISTS_CREDENTIALS.keys()], keys, "credential-persisting checkouts");

console.log(`checkout-credentials: passed (${keys.length} steps scanned, ${PERSISTS_CREDENTIALS.size} persisting)`);
