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
// What it catches, because each makes the run fail: an entry below that no
// longer names exactly one checkout, whether it was renamed, deleted or
// pointed at a different action; a checkout added without
// `persist-credentials`; a checkout that keeps its credential without being
// listed below; a value that is not a YAML boolean; and a listed checkout
// that stopped keeping its credential. Each reports separately, so the
// diagnostic names the actual problem rather than the one it resembles.
import assert from "node:assert/strict";
import { assertExactlyOne, usesSteps } from "./fixtures/workflow-steps.mjs";

// The complete set of checkouts allowed to keep their credential, mapped to
// the reason. Entries are named individually rather than whole files being
// exempted, so a second checkout added to one of these jobs is still reported.
// The reason is not a comment: it is printed on every passing run and quoted
// back when a listed checkout contradicts it, so a stale rationale is visible
// rather than buried.
const PERSISTS_CREDENTIALS = new Map([["release-rust-binaries.yml::homebrew::Check out the Homebrew tap", "the Commit and push formula step pushes to the tap with it"]]);

const CHECKOUT = /^actions\/checkout@/;

const checkouts = [];
const missing = [];
const unlisted = [];
const notBoolean = [];
const contradictory = [];

for (const { key, step } of usesSteps()) {
  if (!CHECKOUT.test(step.uses)) continue;
  checkouts.push(key);

  const value = step.with?.["persist-credentials"];
  const listed = PERSISTS_CREDENTIALS.has(key);
  if (value === undefined) {
    missing.push(key);
  } else if (value !== true && value !== false) {
    // The action decides with `(input || 'false').toUpperCase() === 'TRUE'`,
    // so every value but `true` means false, `yes` and `on` included. Those
    // read as enabling and are not, and a quoted `"true"` enables while
    // looking like a string. Requiring a real YAML boolean keeps the file
    // saying what the action will do.
    notBoolean.push(`${key} (persist-credentials: ${JSON.stringify(value)})`);
  } else if (value === true && !listed) {
    unlisted.push(key);
  } else if (value === false && listed) {
    contradictory.push(`${key} (listed because ${PERSISTS_CREDENTIALS.get(key)})`);
  }
}

// Against the checkouts rather than every `uses:` step, so an exemption has
// to keep naming an `actions/checkout`. Matching any step would let the tap
// step be swapped for another action under the same name: the loop would skip
// it as a non-checkout and the stale exemption would survive unreported.
//
// First, because an exempted step that was renamed, deleted or pointed at
// another action also shows up as an unlisted checkout, and "the exemption
// names nothing" is the cause while "this checkout is not listed" is only the
// symptom.
assertExactlyOne([...PERSISTS_CREDENTIALS.keys()], checkouts, "credential-persisting checkouts");

assert.deepEqual(missing, [], `actions/checkout steps that do not set persist-credentials:\n  ${missing.join("\n  ")}`);
assert.deepEqual(unlisted, [], `actions/checkout steps that keep their credential without being listed in PERSISTS_CREDENTIALS:\n  ${unlisted.join("\n  ")}`);
assert.deepEqual(notBoolean, [], `actions/checkout steps whose persist-credentials is not a YAML boolean:\n  ${notBoolean.join("\n  ")}`);
assert.deepEqual(contradictory, [], `actions/checkout steps listed in PERSISTS_CREDENTIALS that set false, so the entry is stale:\n  ${contradictory.join("\n  ")}`);

console.log(`checkout-credentials: passed (${checkouts.length} checkouts, ${PERSISTS_CREDENTIALS.size} keeping their credential)`);
for (const [key, reason] of PERSISTS_CREDENTIALS) {
  console.log(`  ${key}: ${reason}`);
}
