import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = (name) => readFileSync(new URL("../../" + name, import.meta.url), "utf8");
const manifest = JSON.parse(source("tools/ecmascript-lint/package.json"));
const lock = JSON.parse(source("tools/ecmascript-lint/package-lock.json"));
const workflow = source(".github/workflows/source-policy-toolchain-security.yml");

function assertSupplyChainPolicy(pkg, snapshot, job) {
  assert.equal(snapshot.lockfileVersion, 3, "require an npm v3 frozen lockfile");
  assert.equal(snapshot.packages[""].name, pkg.name, "lock root package identity");
  assert.deepEqual(snapshot.packages[""].dependencies, pkg.dependencies,
    "lock root and manifest dependencies must match exactly");
  assert.ok(Object.keys(snapshot.packages).length > 1, "must lock real dependencies");
  const fixed = {
    minimatch: {
      version: "11.0.3",
      integrity: "sha512-iny/40PEGkNJQ5/Pv6z3nm6FbRAby32GeZRjCUJk2WnNDbgPSTcdI+DDvLqsgBdD4cD5sMtMheqPPnehCCa8Nw==",
    },
    "brace-expansion": {
      version: "5.0.12",
      integrity: "sha512-YovQ3rzhaLMIrDjNDMkNS01tea93qhEhG5xy8f6+R0l+dw3Ki+5sCoIoI942iuLZTHWogWktgwVDhU09iNEimQ==",
    },
    "@isaacs/nonrecursive-glob-match": {
      version: "1.0.3",
      integrity: "sha512-SI7kyKHq4XXDRozw+r9GlRZkia1ZkFrpLW98r2IC2Bpr8YkFGE3fvjzmxCG0x78A++69HmDNrDvSMYBZmHGpKA==",
    },
  };
  assert.deepEqual(pkg.overrides, { minimatch: "11.0.3", "brace-expansion": "5.0.12" },
    "document and pin the intentional cross-major matcher override");
  for (const [name, expected] of Object.entries(fixed)) {
    const path = "node_modules/" + name;
    const entries = Object.entries(snapshot.packages).filter(([key]) =>
      key === path || key.endsWith("/node_modules/" + name));
    assert.equal(entries.length, 1, name + ": no nested vulnerable matcher");
    assert.equal(entries[0][0], path, name + ": fixed matcher must be hoisted");
    const current = entries[0][1];
    assert.equal(current.version, expected.version, name + ": reviewed patched version");
    assert.equal(current.resolved,
      "https://registry.npmjs.org/" + name + "/-/" + name.split("/").at(-1) + "-" + expected.version + ".tgz",
      name + ": reviewed archive URL");
    assert.equal(current.integrity, expected.integrity, name + ": reviewed SHA-512 integrity");
  }
  assert.equal(snapshot.packages["node_modules/minimatch"].dependencies["@isaacs/nonrecursive-glob-match"],
    "^1.0.3", "minimatch 11 requires nonrecursive glob implementation");
  assert.equal(snapshot.packages["node_modules/minimatch"].dependencies["brace-expansion"],
    "^5.0.12", "minimatch 11 must use safe brace expansion");

  for (const [path, details] of Object.entries(snapshot.packages)) {
    if (!path) continue;
    assert.match(details.resolved || "", /^https:\/\/registry\.npmjs\.org\/[^?#]+$/,
      path + " must resolve from a reviewed HTTPS registry archive");
    assert.match(details.integrity || "", /^sha512-[a-zA-Z0-9+/]+={0,2}$/,
      path + " must contain an npm registry archive digest");
  }
  assert.match(job, /^\s+- uses: actions\/checkout@[a-f0-9]{40}(?:\s+#.*)?$/m,
    "pin checkout action to its immutable full SHA");
  assert.ok(job.includes("ref: ${{ github.event.pull_request.head.sha || github.sha }}"),
    "test the actual PR head, not GitHub's synthetic merge ref");
  assert.ok(job.includes('test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"'),
    "assert exact checkout SHA before dependency execution");
  assert.ok(job.includes("EXPECTED_SHA: ${{ github.event.pull_request.head.sha || github.sha }}"),
    "the expected SHA must be the triggering review SHA");
  assert.match(job, /^\s+run: npm ci --ignore-scripts --prefix tools\/ecmascript-lint\s*$/m,
    "install frozen dependencies without lifecycle scripts");
  assert.match(job, /^\s+run: npm audit --audit-level=moderate --prefix tools\/ecmascript-lint\s*$/m,
    "enforce moderate+ audit of the actual sidecar tree");
  assert.match(job, /^\s+run: npm test --prefix tools\/ecmascript-lint\s*$/m,
    "execute parser and policy regressions");
  assert.match(job, /^\s+run: node --test tools\/ecmascript-lint\/minimatch-compat\.test\.mjs\s*$/m,
    "run matcher-11 compatibility checks before accepting cross-major override");
  assert.match(job, /^\s+run: node --test tools\/ecmascript-lint\/lock-security\.test\.mjs\s*$/m,
    "execute offline supply chain regression tests");
  assert.doesNotMatch(job, /continue-on-error:\s*true|--omit=dev|--audit=false|--no-audit|npm audit[^\n]*\|\|\s*(true|:)/,
    "audit must remain blocking, including developer tooling");
}

test("all locked npm archives have HTTPS registry provenance and SHA-512 digests", () => {
  assertSupplyChainPolicy(manifest, lock, workflow);
});

test("mismatched root, missing integrity, unreviewed tarball and empty lock fail closed", () => {
  const rootDrift = structuredClone(lock);
  rootDrift.packages[""].dependencies.eslint = "10.0.0";
  assert.throws(() => assertSupplyChainPolicy(manifest, rootDrift, workflow), /lock root and manifest/);
  const path = Object.keys(lock.packages).find((key) => key);
  for (const [field, replacement] of [["integrity", "sha512-!"], ["integrity", undefined],
    ["resolved", "http://registry.npmjs.org/unsafe.tgz"],
    ["resolved", "https://attacker.invalid/pkg.tgz"]]) {
    const mutant = structuredClone(lock);
    mutant.packages[path][field] = replacement;
    assert.throws(() => assertSupplyChainPolicy(manifest, mutant, workflow));
  }
  const empty = structuredClone(lock);
  empty.packages = { "": structuredClone(lock.packages[""]) };
  assert.throws(() => assertSupplyChainPolicy(manifest, empty, workflow), /lock real dependencies/);
});

test("mutable CI, merge ref, omitted audit, missing tests and audit bypasses fail closed", () => {
  const mutants = [
    workflow.replace("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", "actions/checkout@v4"),
    workflow.replace("ref: ${{ github.event.pull_request.head.sha || github.sha }}", "ref: ${{ github.sha }}"),
    workflow.replace("EXPECTED_SHA: ${{ github.event.pull_request.head.sha || github.sha }}", "EXPECTED_SHA: ${{ github.sha }}"),
    workflow.replace('test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', "echo checked"),
    workflow.replace("npm ci --ignore-scripts --prefix tools/ecmascript-lint", "npm install"),
    workflow.replace("npm audit --audit-level=moderate --prefix tools/ecmascript-lint", "echo ignored"),
    workflow.replace("npm test --prefix tools/ecmascript-lint", "echo skipped"),
    workflow.replace("node --test tools/ecmascript-lint/minimatch-compat.test.mjs", "echo skipped"),
    workflow.replace("node --test tools/ecmascript-lint/lock-security.test.mjs", "echo skipped"),
    workflow + "\n      - name: Disable audit\n        continue-on-error: true\n",
    workflow + "\n      - name: Ignore dev audit\n        run: npm audit --omit=dev\n",
    workflow + "\n      - name: Hide audit errors\n        run: npm audit --audit-level=moderate || true\n",
  ];
  for (const [index, mutant] of mutants.entries()) {
    assert.notEqual(mutant, workflow, "mutation #" + index + " must change workflow");
    assert.throws(() => assertSupplyChainPolicy(manifest, lock, mutant),
      undefined, "admitted invalid CI mutation #" + index);
  }
});

test("patch floors reject stale minimatch, bogus digests, hidden nested copies and removed overrides", () => {
  for (const [name, old] of [["minimatch", "10.2.6"], ["brace-expansion", "5.0.9"],
    ["@isaacs/nonrecursive-glob-match", "0.0.1"]]) {
    const downgraded = structuredClone(lock);
    downgraded.packages["node_modules/" + name].version = old;
    assert.throws(() => assertSupplyChainPolicy(manifest, downgraded, workflow),
      /reviewed patched version/);
    const tampered = structuredClone(lock);
    tampered.packages["node_modules/" + name].integrity = "sha512-wrong";
    assert.throws(() => assertSupplyChainPolicy(manifest, tampered, workflow),
      /reviewed SHA-512 integrity/);
    const nested = structuredClone(lock);
    nested.packages["node_modules/eslint/node_modules/" + name] =
      { ...nested.packages["node_modules/" + name], version: old };
    assert.throws(() => assertSupplyChainPolicy(manifest, nested, workflow),
      /no nested vulnerable matcher/);
  }
  for (const overrides of [{}, { minimatch: "11.0.3" },
    { minimatch: "^11.0.3", "brace-expansion": "5.0.12" },
    { minimatch: "10.2.6", "brace-expansion": "5.0.12" }]) {
    assert.throws(() => assertSupplyChainPolicy({ ...manifest, overrides }, lock, workflow),
      /cross-major matcher override/);
  }
});
