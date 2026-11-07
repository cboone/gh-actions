import assert from "node:assert/strict";

export function parseFindings(output) {
  assert.ok(typeof output === "string", "fingerprint report must be text");
  assert.ok(output.trim(), "fingerprint report must contain JSON");
  let findings;
  try {
    findings = JSON.parse(output);
  } catch {
    assert.fail("fingerprint report must contain valid JSON");
  }
  assert.ok(Array.isArray(findings), "fingerprint report must be an array");
  for (const finding of findings) {
    assert.ok(finding !== null && typeof finding === "object" && !Array.isArray(finding), "fingerprint finding must be an object");
    assert.ok(typeof finding.File === "string", "fingerprint finding must have a string File");
    assert.ok(typeof finding.Fingerprint === "string", "fingerprint finding must have a string Fingerprint");
  }
  return findings;
}
