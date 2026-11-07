// Execute the workflow's scan block with real gitleaks and disposable PR histories.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdtempSync, mkdirSync, rmSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { loadWorkflow, stepOf, runStepScript } from "./fixtures/workflow-steps.mjs";
import { parseFindings } from "./fixtures/gitleaks-findings.mjs";
import "./check-gitleaks-findings.mjs";

const workflow = loadWorkflow("scan-for-secrets.yml");
const steps = workflow.jobs.gitleaks.steps;
const scan = stepOf(workflow, "gitleaks", "Run gitleaks");
const checkout = stepOf(workflow, "gitleaks", "Check out trusted gitleaks configuration");
assert.equal(checkout.if, "github.event_name == 'pull_request'");
assert.equal(checkout.with.repository, "${{ github.repository }}");
assert.equal(checkout.with.ref, "${{ github.event.pull_request.base.sha }}");
assert.equal(checkout.with.path, "gitleaks-base");
assert.equal(checkout.with["persist-credentials"], false);
assert.equal(steps[0].with.path, "gitleaks-source");
assert.equal(steps[0].with["persist-credentials"], false);
assert.equal(scan["working-directory"], "gitleaks-source");
assert.equal(scan.env.EVENT_NAME, "${{ github.event_name }}");
assert.equal(scan.env.ALLOWLIST_CONFIG, "${{ inputs.allowlist-config }}");
assert.equal(scan.env.SCAN_SCOPE, "${{ inputs.scan-scope }}");
const helperCheckout = stepOf(workflow, "gitleaks", "Check out trusted gitleaks helpers");
assert.equal(helperCheckout.if, "github.event_name == 'pull_request'");
assert.equal(helperCheckout.with.repository, "${{ job.workflow_repository }}");
assert.equal(helperCheckout.with.ref, "${{ job.workflow_sha }}");
assert.equal(helperCheckout.with["persist-credentials"], false);
assert.equal(helperCheckout.with.path, "gitleaks-tools");
assert.equal(scan.env.PREPARE_CONFIG, "${{ github.workspace }}/gitleaks-tools/scripts/prepare-gitleaks-config.py");
const uv = stepOf(workflow, "gitleaks", "Set up uv for trusted config preparation");
assert.equal(uv.if, "github.event_name == 'pull_request'");
assert.equal(uv.uses, "./gitleaks-tools/actions/set-up-uv");
const contextGuard = stepOf(workflow, "gitleaks", "Validate trusted gitleaks helper context");
assert.equal(contextGuard.if, "github.event_name == 'pull_request'");
assert.equal(contextGuard.env.REQ_REPO, "${{ job.workflow_repository }}");
assert.equal(contextGuard.env.REQ_SHA, "${{ job.workflow_sha }}");
assert.ok(steps.indexOf(contextGuard) < steps.indexOf(helperCheckout), "context guard must precede helper checkout");
assert.equal(stepOf(loadWorkflow("run-ci.yml"), "gitleaks-base-config", "Install uv for gitleaks fixtures").uses, "./actions/set-up-uv", "gitleaks fixtures require pinned uv installation");
const prepareConfig = resolve("scripts/prepare-gitleaks-config.py");

const defaults = "[extend]\nuseDefault = true\n";
const widened = `${defaults}\n[allowlist]\npaths = ['''.*''']\n`;
// Synthetic token assembled at runtime so the self-scan does not flag this fixture.
const secret = `token = "${"ghp_"}${randomBytes(18).toString("hex")}"\n`;
const root = mkdtempSync(join(tmpdir(), "gitleaks-base-control-"));
let cases = 0;

function git(cwd, args, input) {
  const result = spawnSync("git", ["-c", "gc.auto=0", "-c", "maintenance.auto=false", ...args], { cwd, input, encoding: "utf8" });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
}

function commit(files, mark, parent = "") {
  let stream = `commit refs/heads/main\nmark :${mark}\ncommitter Fixture <fixture@example.invalid> ${1700000000 + mark} +0000\ndata 7\nfixture\n${parent ? `from ${parent}\n` : ""}`;
  for (const [path, entry] of Object.entries(files)) {
    if (entry === null) {
      stream += `D ${JSON.stringify(path)}\n`;
      continue;
    }
    const { mode, content } = typeof entry === "string" ? { mode: "100644", content: entry } : entry;
    stream += `M ${mode} inline ${JSON.stringify(path)}\ndata ${Buffer.byteLength(content)}\n${content}\n`;
  }
  return `${stream}\n`;
}

function runCase(name, { base = {}, head = {}, config = "", event = "pull_request", scope = "working-tree", expected = 1, expectSecret = false, secretPath = "secret.txt", historyOnly = false, prIgnore = false, message = "leaks found: [1-9]" } = {}) {
  const workspace = join(root, name);
  const source = join(workspace, "gitleaks-source");
  const temp = join(workspace, "temp");
  mkdirSync(source, { recursive: true });
  mkdirSync(temp);
  git(source, ["init", "--quiet"]);
  const baseFiles = { "README.md": "clean fixture\n", ...base };
  git(source, ["fast-import", "--quiet"], `${commit(baseFiles, 1)}${commit({ [secretPath]: secret, ...head }, 2)}${historyOnly ? commit({ [secretPath]: null }, 3) : ""}done\n`);
  const baseSha = git(source, ["rev-parse", historyOnly ? "main~2" : "main^"]);
  git(source, ["checkout", "--quiet", "main"]);
  if (prIgnore) {
    const probeConfig = join(temp, "probe.toml");
    writeFileSync(probeConfig, defaults);
    const probeArgs = ["detect", "--source", ".", "--config", probeConfig, "--report-format", "json", "--report-path", "-", "--redact"];
    if (scope === "working-tree") probeArgs.push("--no-git");
    const probe = spawnSync("gitleaks", probeArgs, { cwd: source, encoding: "utf8" });
    assert.ifError(probe.error);
    assert.equal(probe.status, 1, `${name}: fingerprint probe must detect the secret`);
    const findings = parseFindings(probe.stdout).filter((finding) => finding.File === secretPath);
    assert.ok(findings.length > 0, `${name}: fingerprint probe must report the secret file`);
    const oldHead = git(source, ["rev-parse", "main"]);
    git(source, ["checkout", "--quiet", "--detach", baseSha]);
    git(source, ["fast-import", "--quiet"], `${commit({ ".gitleaksignore": findings.map((finding) => finding.Fingerprint).join("\n") + "\n" }, 4, oldHead)}done\n`);
    git(source, ["checkout", "--quiet", "main"]);
  }
  git(source, ["worktree", "add", "--quiet", "--detach", join(workspace, "gitleaks-base"), baseSha]);
  const originalIgnore = existsSync(join(source, ".gitleaksignore")) ? readFileSync(join(source, ".gitleaksignore"), "utf8") : null;
  const result = runStepScript(scan.run, {
    cwd: source,
    env: { ...process.env, GITHUB_WORKSPACE: workspace, RUNNER_TEMP: temp, EVENT_NAME: event, ALLOWLIST_CONFIG: config, SCAN_SCOPE: scope, PREPARE_CONFIG: prepareConfig },
  });
  assert.equal(result.status, expected, `${name}: unexpected scan exit\n${result.output}`);
  assert.match(result.output, new RegExp(message), `${name}: expected diagnostic\n${result.output}`);
  if (expectSecret) assert.ok(result.output.includes(secretPath), `${name}: planted secret was not detected`);
  if (originalIgnore !== null) {
    assert.ok(existsSync(join(source, ".gitleaksignore")), `${name}: ignore file was not restored`);
    assert.equal(readFileSync(join(source, ".gitleaksignore"), "utf8"), originalIgnore, `${name}: ignore file was not restored`);
  }
  cases++;
  console.log(`gitleaks-base-config: ${name}: passed`);
}

try {
  for (const scope of ["working-tree", "full-history"]) {
    runCase(`added-default-${scope}`, { head: { ".gitleaks.toml": widened }, scope, expectSecret: true });
    runCase(`edited-default-${scope}`, { base: { ".gitleaks.toml": defaults }, head: { ".gitleaks.toml": widened }, scope, expectSecret: true });
    runCase(`explicit-${scope}`, { base: { "config/allow list.toml": defaults }, head: { "config/allow list.toml": widened, ".gitleaks.toml": widened }, config: "config/allow list.toml", scope, expectSecret: true });
    runCase(`extended-${scope}`, { base: { ".gitleaks.toml": '[extend]\npath = "rules.toml"\n', "rules.toml": defaults }, head: { "rules.toml": widened }, scope, expectSecret: true });
  }
  runCase("base-allowlist", { base: { ".gitleaks.toml": widened }, expected: 0, message: "no leaks found" });
  runCase("clean", { head: { "secret.txt": "clean\n", ".gitleaks.toml": widened }, expected: 0, message: "no leaks found" });
  runCase("push-auto-discovery", { head: { ".gitleaks.toml": widened }, event: "push", expected: 0, message: "no leaks found" });
  runCase("push-explicit", { head: { "config.toml": widened }, config: "config.toml", event: "push", expected: 0, message: "no leaks found" });
  runCase("missing-explicit", { head: { "new.toml": widened }, config: "new.toml", message: "within the base checkout" });
  runCase("absolute-path", { config: "/tmp/config.toml", message: "must be relative" });
  runCase("escaping-path", { config: "../gitleaks-source/.gitleaks.toml", head: { ".gitleaks.toml": widened }, message: "within the base checkout" });
  runCase("directory", { config: ".", message: "within the base checkout" });
  for (const [repo, sha, expected] of [
    ["", "a".repeat(40), 1],
    ["cboone/gh-actions", "", 1],
    ["", "", 1],
    ["cboone/gh-actions", "a".repeat(40), 0],
  ]) {
    const result = runStepScript(contextGuard.run, { cwd: root, env: { ...process.env, REQ_REPO: repo, REQ_SHA: sha } });
    assert.equal(result.status, expected, "trusted helper context must fail closed on missing values");
    cases++;
  }
  const escapedRule = String.raw`[[rules]]
id = "escaped-control"
regex = '''\bfixture_key\s*=\s*([A-Z]{4}\d{4})\b'''
secretGroup = 1
path = "^src/"
`;
  const scopedRule = '[[rules]]\nid = "path-control"\nregex = "token"\npath = "^src/"\n';
  for (const event of ["pull_request", "push"]) {
    runCase(`anchored-rule-${event}`, { base: { ".gitleaks.toml": scopedRule }, event, secretPath: "src/secret.txt", expectSecret: true });
    runCase(`anchored-allowlist-${event}`, { base: { ".gitleaks.toml": `${defaults}\n[allowlist]\npaths = ['''^src/''']\n` }, event, secretPath: "src/secret.txt", expected: 0, message: "no leaks found" });
  }
  runCase("escaped-regex", { base: { ".gitleaks.toml": escapedRule }, secretPath: "src/secret.txt", head: { "src/secret.txt": "fixture_key = ABCD1234\n" }, expectSecret: true });
  // Preserve the key spelling: Go and Python case mappings differ here.
  // cspell:ignore condİtİon
  const unicodeRule = `[[rules]]
id = "unicode-control"
regex = "fixture-canary"
[[rules.allowlists]]
"condİtİon" = "AND"
paths = ["^never$"]
regexes = ["fixture-canary"]
`;
  runCase("unicode-key-semantics", { base: { ".gitleaks.toml": unicodeRule }, secretPath: "src/secret.txt", head: { "src/secret.txt": "fixture-canary\n" }, expectSecret: true });
  runCase("history-only-full-history", { historyOnly: true, scope: "full-history", expectSecret: true });
  runCase("history-only-working-tree", { historyOnly: true, expected: 0, message: "no leaks found" });
  runCase("external-config-symlink", { base: { ".gitleaks.toml": { mode: "120000", content: "../gitleaks-source/evil.toml" } }, head: { "evil.toml": widened }, message: "within the base checkout" });
  runCase("internal-config-symlink", { base: { ".gitleaks.toml": { mode: "120000", content: "rules.toml" }, "rules.toml": defaults }, expectSecret: true });
  runCase("dangling-config-symlink", { base: { ".gitleaks.toml": { mode: "120000", content: "missing.toml" } }, message: "within the base checkout" });
  runCase("external-extension-symlink", { base: { ".gitleaks.toml": '[extend]\npath = "rules.toml"\n', "rules.toml": { mode: "120000", content: "../gitleaks-source/evil.toml" } }, head: { "evil.toml": widened }, message: "within the base checkout" });
  runCase("extension-chain", { base: { ".gitleaks.toml": '[Extend]\nPath = "rules.toml"\n', "rules.toml": '[extend]\npath = "final.toml"\n', "final.toml": '[[rules]]\nid = "chain-control"\nregex = "token"\n' }, head: { "rules.toml": widened, "final.toml": widened }, expectSecret: true });
  runCase("cyclic-extension", { base: { ".gitleaks.toml": '[extend]\npath = ".gitleaks.toml"\n' }, message: "Cyclic or over-depth" });
  runCase("invalid-toml", { base: { ".gitleaks.toml": "[invalid" }, message: "Invalid TOML" });
  runCase("external-ignore-symlink", { base: { ".gitleaksignore": { mode: "120000", content: "../gitleaks-source/ignored" } }, head: { ignored: "secret.txt:github-pat:1\n" }, message: "within the base checkout" });
  runCase("ambiguous-keys", { base: { ".gitleaks.toml": '[extend]\nuseDefault = true\n[Extend]\nPath = "rules.toml"\n', "rules.toml": widened }, message: "duplicate case-insensitive" });
  runCase("empty-restore", { head: { ".gitleaksignore": "unmatched\n", "secret.txt": "clean\n" }, expected: 0, message: "no leaks found" });
  runCase("trusted-ignore", { base: { ".gitleaksignore": "secret.txt:github-pat:1\nsecret.txt:generic-api-key:1\n" }, expected: 0, message: "no leaks found" });
  for (const scope of ["working-tree", "full-history"]) {
    runCase(`proposed-ignore-${scope}`, { prIgnore: true, scope, expectSecret: true });
  }
  runCase("proposed-ignore-push", { prIgnore: true, event: "push", expected: 0, message: "no leaks found" });
  runCase("ignore-content", { secretPath: ".gitleaksignore", expectSecret: true });
  console.log(`gitleaks-base-config: passed (${cases} cases)`);
} finally {
  // Only this fixture's recorded, exclusively owned directory is removed.
  rmSync(root, { recursive: true });
}
