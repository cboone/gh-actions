import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadWorkflow, runStepScript, stepOf } from "./workflow-steps.mjs";

// The two publish workflows and the Pages build share an install step and a
// lockfile probe, and the two publish workflows carry permission blocks that
// nothing else can check: no CI job can call either of them end to end without
// a publishable package to point it at. This fixture runs the production steps
// against stubs and asserts the rest statically.

const tokenPublish = loadWorkflow("publish-to-npm.yml");
const oidcPublish = loadWorkflow("publish-to-npm-with-oidc.yml");
const pages = loadWorkflow("deploy-to-pages.yml");

const registryStep = stepOf(oidcPublish, "publish", "Check the registry");
const versionStep = stepOf(oidcPublish, "publish", "Check npm and Node versions");
const detectSteps = [
  ["publish-to-npm.yml", stepOf(tokenPublish, "publish", "Detect lockfile")],
  ["publish-to-npm-with-oidc.yml", stepOf(oidcPublish, "publish", "Detect lockfile")],
];
const installSteps = [
  ["publish-to-npm.yml", stepOf(tokenPublish, "publish", "Install dependencies")],
  ["publish-to-npm-with-oidc.yml", stepOf(oidcPublish, "publish", "Install dependencies")],
  ["deploy-to-pages.yml", stepOf(pages, "build", "Install dependencies")],
];

// Defaults and minimums come from the workflows, so a scenario cannot drift
// from what callers actually get.
const shippedRegistry = oidcPublish.on.workflow_call.inputs["registry-url"].default;
const tokenRegistry = tokenPublish.on.workflow_call.inputs["registry-url"].default;
const minimumNode = versionStep.env.MINIMUM_NODE;
const minimumNpm = versionStep.env.MINIMUM_NPM;
const nodeForNpm = versionStep.env.NODE_FOR_NPM;

const root = mkdtempSync(join(tmpdir(), "npm-publish-"));
const binDir = join(root, "bin");
const argvFile = join(root, "argv.txt");

// Records the argument vector it was handed, one element per line, which is the
// only way to see argument boundaries from outside the process.
function installArgvStub(name) {
  const path = join(binDir, name);
  writeFileSync(path, ["#!/bin/sh", ': > "${ARGV_FILE}"', 'for arg in "$@"; do', '  printf \'%s\\n\' "${arg}" >> "${ARGV_FILE}"', "done", ""].join("\n"));
  chmodSync(path, 0o755);
}

function installVersionStub(name, version) {
  const path = join(binDir, name);
  writeFileSync(path, ["#!/bin/sh", `printf '%s\\n' '${version}'`, ""].join("\n"));
  chmodSync(path, 0o755);
}

function runStep(step, { env = {}, cwd = root } = {}) {
  rmSync(argvFile, { force: true });
  const result = runStepScript(step.run, {
    cwd,
    env: { ...process.env, ...env, PATH: `${binDir}:${process.env.PATH}`, ARGV_FILE: argvFile },
  });
  const argv = existsSync(argvFile) ? readFileSync(argvFile, "utf8").split("\n").slice(0, -1) : null;
  return { ...result, argv };
}

function expectAccepted(result, label) {
  assert.equal(result.status, 0, `${label}: ${result.output}`);
}

function expectRejected(result, diagnostic, label) {
  assert.equal(result.status, 1, `${label} was accepted:\n${result.output}`);
  assert.ok(result.output.includes(diagnostic), `${label}: ${result.output}`);
}

function registry(url) {
  return runStep(registryStep, { env: { REGISTRY_URL: url } });
}

function versions({ node = `v${minimumNode}`, npm = minimumNpm } = {}) {
  installVersionStub("node", node);
  installVersionStub("npm", npm);
  return runStep(versionStep, { env: versionStep.env });
}

// A fresh working directory per case, since the lockfile probe and `npm ci`
// both read the one they run in.
function workspace(files = {}) {
  const dir = mkdtempSync(join(root, "workspace-"));
  for (const [name, contents] of Object.entries(files)) writeFileSync(join(dir, name), contents);
  return dir;
}

function install(step, { lockfile = "", allow = "false", scripts = "false" } = {}) {
  installArgvStub("npm");
  return runStep(step, {
    cwd: workspace(),
    env: { LOCKFILE: lockfile, ALLOW_NPM_INSTALL: allow, RUN_INSTALL_SCRIPTS: scripts },
  });
}

function setupNodeStep(workflow, job) {
  const steps = workflow.jobs[job].steps.filter((step) => typeof step.uses === "string" && step.uses.startsWith("actions/setup-node@"));
  assert.equal(steps.length, 1, `expected exactly one setup-node step in ${job}`);
  return steps[0];
}

const scenarios = {
  // The likeliest misconfiguration is carrying the token workflow's GitHub
  // Packages default across to the OIDC one.
  registry() {
    expectAccepted(registry(shippedRegistry), "the shipped default");
    expectAccepted(registry("https://registry.npmjs.org"), "the npmjs registry");
    expectAccepted(registry("https://registry.npmjs.org/"), "a trailing slash");
    expectRejected(registry(tokenRegistry), "publish-to-npm.yml", "the GitHub Packages default");
    expectRejected(registry("https://registry.npmjs.org.example.com"), "registry-url must be", "a lookalike host");
    expectRejected(registry(""), "registry-url must be", "an empty registry");
  },

  // Below these versions npm has no OIDC support and reports only that
  // authentication failed, which is the confusion the gate exists to prevent.
  versions() {
    expectAccepted(versions(), "the exact minimums");
    expectAccepted(versions({ node: "v24.21.0", npm: "11.6.2" }), "versions above the minimums");
    expectAccepted(versions({ node: "v23" }), "a version with fewer fields");
    // A prerelease of a higher version clears the minimum; a prerelease of the
    // minimum itself does not, since it precedes the release that carries the
    // support the gate is checking for.
    expectAccepted(versions({ npm: "12.0.0-rc.1" }), "a prerelease above the minimum");
    expectRejected(versions({ npm: `${minimumNpm}-rc.1` }), `below ${minimumNpm}`, "a prerelease of the minimum npm");
    expectRejected(versions({ node: `v${minimumNode}-nightly` }), `below ${minimumNode}`, "a prerelease of the minimum Node");
    expectRejected(versions({ node: "v22.13.9" }), `below ${minimumNode}`, "an old Node");
    expectRejected(versions({ node: "v20.19.5" }), "node-version", "a Node major behind");
    expectRejected(versions({ npm: "11.5.0" }), `below ${minimumNpm}`, "an old npm");
    expectRejected(versions({ npm: "9.9.9" }), `node-version ${nodeForNpm}`, "an npm major behind");
    // The Node floor npm documents is not enough on its own: no Node 22 or
    // 23 release bundles an npm this new, so the message names a Node that
    // does rather than telling the caller to raise a version that cannot help.
    expectRejected(versions({ node: `v${minimumNode}`, npm: "10.9.2" }), `node-version ${nodeForNpm}`, "the npm bundled with the minimum Node");
  },

  // The probe names the lockfile the install step keys off.
  detect() {
    for (const [label, step] of detectSteps) {
      for (const [files, expected] of [
        [{ "package-lock.json": "{}" }, "path=package-lock.json"],
        [{ "npm-shrinkwrap.json": "{}" }, "path=npm-shrinkwrap.json"],
        [{ "package-lock.json": "{}", "npm-shrinkwrap.json": "{}" }, "path=package-lock.json"],
        [{}, "path="],
      ]) {
        const cwd = workspace(files);
        const outputFile = join(cwd, "github-output");
        writeFileSync(outputFile, "");
        const result = runStep(step, { cwd, env: { GITHUB_OUTPUT: outputFile } });
        assert.equal(result.status, 0, `${label}: ${result.output}`);
        assert.equal(readFileSync(outputFile, "utf8").trim(), expected, `${label} with ${JSON.stringify(Object.keys(files))}`);
      }
    }
  },

  // A lockfile is installed from; its absence is an error the caller has to
  // answer for, and lifecycle scripts stay off unless asked for.
  install() {
    const locked = ["ci", "--include=dev", "--no-audit", "--no-fund", "--ignore-scripts"];
    for (const [label, step] of installSteps) {
      let result = install(step, { lockfile: "package-lock.json" });
      assert.equal(result.status, 0, `${label}: ${result.output}`);
      assert.deepEqual(result.argv, locked, `${label} with a lockfile`);

      result = install(step, { lockfile: "npm-shrinkwrap.json" });
      assert.deepEqual(result.argv, locked, `${label} with a shrinkwrap`);

      result = install(step, { allow: "true" });
      assert.equal(result.status, 0, `${label}: ${result.output}`);
      assert.deepEqual(result.argv, ["install", "--include=dev", "--no-audit", "--no-fund", "--ignore-scripts"], `${label} without a lockfile, opted in`);
      assert.ok(result.output.includes("::warning::"), `${label} fell back without saying so:\n${result.output}`);

      result = install(step, { lockfile: "package-lock.json", scripts: "true" });
      assert.deepEqual(result.argv, ["ci", "--include=dev", "--no-audit", "--no-fund"], `${label} with scripts enabled`);

      result = install(step);
      assert.equal(result.status, 1, `${label} installed without a lockfile:\n${result.output}`);
      assert.equal(result.argv, null, `${label} ran npm despite refusing the install`);
      assert.ok(result.output.includes("allow-npm-install"), `${label}: ${result.output}`);

      // Anything other than the literal true is not an opt-in.
      result = install(step, { allow: "yes" });
      assert.equal(result.status, 1, `${label} treated "yes" as an opt-in`);
      result = install(step, { lockfile: "package-lock.json", scripts: "1" });
      assert.deepEqual(result.argv, locked, `${label} treated "1" as an opt-in`);
    }
  },

  // A reusable workflow cannot reach a repository-owned composite action by a
  // `./` path, so these blocks are copies. Nothing but this keeps them honest.
  parity() {
    const [first, ...rest] = installSteps;
    for (const [label, step] of rest) {
      assert.equal(step.run, first[1].run, `the install step in ${label} has drifted from ${first[0]}`);
    }
    assert.equal(detectSteps[1][1].run, detectSteps[0][1].run, "the lockfile probes in the two publish workflows have drifted");
  },

  // What separates the two publish workflows: each declares only the permission
  // its auth mode can use. A caller must grant everything the workflow it calls
  // declares, and a nested job's permissions are checked before its `if:` is
  // evaluated, so merging these two files would put `id-token: write` on every
  // token-path caller.
  shape() {
    assert.deepEqual(oidcPublish.permissions, { contents: "read", "id-token": "write" });
    assert.deepEqual(tokenPublish.permissions, { contents: "read", packages: "write" });

    assert.equal(oidcPublish.on.workflow_call.secrets, undefined, "the OIDC workflow declares a secret");
    // Every environment binding in the file, so a token cannot reach it by any
    // step. Checking the source text instead would be defeated by a comment
    // explaining the absence.
    const oidcBindings = JSON.stringify([oidcPublish.env ?? null, ...Object.values(oidcPublish.jobs).flatMap((job) => [job.env ?? null, ...(job.steps ?? []).map((step) => step.env ?? null)])]);
    assert.ok(!oidcBindings.includes("NODE_AUTH_TOKEN"), "the OIDC workflow binds NODE_AUTH_TOKEN");
    assert.ok(!oidcBindings.includes("secrets."), "the OIDC workflow reads a secret");
    assert.equal(tokenPublish.on.workflow_call.secrets.NODE_AUTH_TOKEN.required, true);
    assert.equal(stepOf(tokenPublish, "publish", "Publish").env.NODE_AUTH_TOKEN, "${{ secrets.NODE_AUTH_TOKEN }}");
    assert.equal(stepOf(oidcPublish, "publish", "Publish").env, undefined, "the OIDC publish step binds an environment");

    // Only ever set to false: npm reads an env config set to the empty string
    // as true, and an explicit true turns npm's automatic skip for a restricted
    // package into a hard error.
    const provenance = stepOf(oidcPublish, "publish", "Disable provenance");
    assert.equal(provenance.if, "${{ !inputs.provenance }}");
    assert.ok(provenance.run.includes("NPM_CONFIG_PROVENANCE=false"));

    // A caller cannot pass an environment to a reusable workflow, and the OIDC
    // `environment` claim comes from the job that mints the token, which is
    // this one. Without the input, a publisher scoped to an environment is
    // unreachable; with it, the default of "" leaves the claim absent.
    assert.equal(oidcPublish.jobs.publish.environment, "${{ inputs.environment }}");
    assert.equal(oidcPublish.on.workflow_call.inputs.environment.default, "");
    assert.equal(tokenPublish.jobs.publish.environment, undefined, "the token workflow declares an environment");

    // A publish must not restore a cache an earlier job wrote. Clearing
    // `cache:` is not enough, because setup-node caches on its own whenever
    // package.json names npm in packageManager or devEngines.packageManager.
    for (const [label, workflow, job] of [
      ["publish-to-npm.yml", tokenPublish, "publish"],
      ["publish-to-npm-with-oidc.yml", oidcPublish, "publish"],
    ]) {
      const step = setupNodeStep(workflow, job);
      assert.equal(step.with["package-manager-cache"], false, `${label} leaves setup-node's own caching on`);
      assert.equal(step.with.cache, undefined, `${label} sets a cache during a publish`);
    }

    // The Pages build is not a publish, and keeps its cache.
    assert.equal(setupNodeStep(pages, "build").with.cache, "${{ steps.npm-cache.outputs.cache }}");
  },
};

const name = process.argv[2];
const scenario = scenarios[name];
if (!scenario) throw new Error(`Unknown scenario: ${name}`);

try {
  mkdirSync(binDir, { recursive: true });
  scenario();
  console.log(`${name}: passed`);
} finally {
  rmSync(root, { recursive: true, force: true });
}
