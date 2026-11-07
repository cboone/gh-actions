import assert, { AssertionError } from "node:assert/strict";
import { parseFindings } from "./fixtures/gitleaks-findings.mjs";
import { assertionLabel } from "./fixtures/gitleaks-assertion-verdict.mjs";

assert.throws(() => parseFindings("{}"), { code: "ERR_ASSERTION", message: "fingerprint report must be an array" }, "fingerprint report shape guard must reject a non-array with a named assertion");
for (const [input, message] of [
  [null, "fingerprint report must be text"],
  ["", "fingerprint report must contain JSON"],
  ["{", "fingerprint report must contain valid JSON"],
  ["[null]", "fingerprint finding must be an object"],
  ['[{"File":1,"Fingerprint":"abc"}]', "fingerprint finding must have a string File"],
  ['[{"File":"file.txt"}]', "fingerprint finding must have a string Fingerprint"],
]) {
  assert.throws(() => parseFindings(input), { code: "ERR_ASSERTION", message });
}
assert.deepEqual(parseFindings("[]"), []);
assert.deepEqual(parseFindings('[{"File":"file.txt","Fingerprint":"abc"}]'), [{ File: "file.txt", Fingerprint: "abc" }]);

const label = "added-default-working-tree: unexpected scan exit";
assert.equal(assertionLabel(new AssertionError({ message: label })), label);
assert.equal(assertionLabel({ code: "ERR_ASSERTION", message: label }), null, "verdict adapter must reject counterfeit assertion objects");
assert.equal(assertionLabel(new TypeError(label)), null);
assert.equal(assertionLabel(new AssertionError({ message: "unmapped assertion" })), null);
assert.equal(assertionLabel(null), null);
console.log("gitleaks fingerprint parser and assertion verdict controls completed");
