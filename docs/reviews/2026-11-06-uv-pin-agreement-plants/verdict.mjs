import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
console.log("uv pin assertion reached");
const result = spawnSync(process.execPath, ["tests/fixtures/check-workflow-arg-binding.mjs", "tool-pins"], { encoding: "utf8" });
assert.ifError(result.error);
assert.equal(result.signal, null);
if (result.status === 0) {
  assert.equal(result.stdout, "tool-pins: passed\n");
  console.log("uv pin verdict: agree");
} else {
  assert.equal(result.status, 1);
  assert.ok(result.stderr.includes("AssertionError") && result.stderr.includes("uv pins disagree:"), result.stderr);
  console.log("uv pin verdict: disagree");
  process.exitCode = 1;
}
