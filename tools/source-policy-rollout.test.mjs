import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const file = new URL('../.github/workflows/source-policy-lint.yml', import.meta.url);
const workflow = readFileSync(file, 'utf8');
const approvedCandidate = 'cbfd81cd53bf139ae3552932ca05ee30686d1460';
const expression = '$' + '{{ github.event.pull_request.head.sha || github.sha }}';

function admission(source) {
  assert.match(source, /^permissions:\n  contents: read$/m,
    'reusable workflow cannot gain write token permissions');
  assert.match(source, /^  workflow_call:$/m,
    'reusable entrypoint remains callable');
  assert.ok(source.includes('      - tools/source-policy-rollout.test.mjs'),
    'test updates must trigger the upstream workflow');
  const checkouts = source.match(/^\s+uses: actions\/checkout@([^\s]+)/gm) || [];
  assert.equal(checkouts.length, 2, 'caller and policy checkouts both required');
  for (const line of checkouts) {
    assert.match(line, /actions\/checkout@[a-f0-9]{40}/,
      'both checkout actions must be immutable');
  }
  assert.ok(source.includes('          ref: ' + expression),
    'checkout must select original PR SHA, not a synthetic merge ref');
  assert.ok(source.includes('          EXPECTED_SHA: ' + expression),
    'expected SHA must bind to the original PR SHA');
  assert.ok(source.includes('          test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"'),
    'must compare expected and checked out SHA');
  assert.ok(source.includes("          git rev-parse 'HEAD^{tree}'"),
    'must report audited tree');
  assert.equal(source.split('          ref: ' + approvedCandidate).length, 2,
    'the reviewed central policy implementation must be pinned at exactly one SHA');
  assert.ok(source.includes('          repository: ores-otel/.github'),
    'fetch the central policy implementation from its source repository');
  const credentialRules = source.match(/^\s+persist-credentials:\s*(true|false)$/gm) || [];
  assert.equal(credentialRules.length, checkouts.length,
    'every caller/policy checkout needs its own explicit credentials policy');
  assert.equal(credentialRules.every((line) => line.trim() === 'persist-credentials: false'), true,
    'all checkouts must avoid persistent repository credentials');
  assert.match(source, /^\s+run: npm ci --ignore-scripts --prefix \.source-policy\/tools\/ecmascript-lint$/m,
    'frozen source policy installation is mandatory');
  const installed = 'npm ls minimatch brace-expansion @isaacs/nonrecursive-glob-match --all --prefix .source-policy/tools/ecmascript-lint';
  const audit = 'npm audit --audit-level=moderate --prefix .source-policy/tools/ecmascript-lint';
  const lint = 'node .source-policy/tools/ecmascript-lint/lint.mjs "$GITHUB_WORKSPACE"';
  for (const command of [
    installed, audit, lint,
    'npm test --prefix .source-policy/tools/ecmascript-lint',
    'node --test .source-policy/tools/ecmascript-lint/minimatch-compat.test.mjs',
    'node --test .source-policy/tools/ecmascript-lint/lock-security.test.mjs',
    'node --test tools/source-policy-rollout.test.mjs',
  ]) {
    assert.ok(source.includes(command), 'required stage missing: ' + command);
  }
  const install = source.indexOf('npm ci --ignore-scripts --prefix .source-policy/tools/ecmascript-lint');
  assert.ok(install > 0 && install < source.indexOf(installed) &&
    source.indexOf(installed) < source.indexOf(audit) &&
    source.indexOf(audit) < source.indexOf(lint),
  'frozen install, installed graph check and audit must precede lint execution');
  assert.ok(source.includes("if: github.repository == 'ores-otel/.github' && steps.languages.outputs.ecmascript == 'true'"),
    'only the owning repository should execute its local staged-rollout test');
  assert.doesNotMatch(source,
    /continue-on-error:\s*true|--audit=false|--no-audit|--omit=dev|--production|npm audit[^\n]*\|\|\s*(?:true|:)/,
    'no bypass of the nested developer-dependency audit');
}

test('staged reusable source-policy workflow enforces exact-head, patched pin and nested advisory gate', () => {
  admission(workflow);
});

test('negative mutation: disabled audit, stale SHA and substituted merge ref are rejected', () => {
  const changes = [
    ['ref: ' + expression, 'ref: ' + '$' + '{{ github.sha }}'],
    ['EXPECTED_SHA: ' + expression, 'EXPECTED_SHA: ' + '$' + '{{ github.sha }}'],
    ['test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', 'echo no commit verification'],
    ['ref: ' + approvedCandidate, 'ref: 9e2a95413dafbef326ef3e93943a30c22566cc01'],
    ['npm ci --ignore-scripts --prefix .source-policy/tools/ecmascript-lint', 'npm install --prefix .source-policy/tools/ecmascript-lint'],
    ['npm ls minimatch brace-expansion @isaacs/nonrecursive-glob-match --all --prefix .source-policy/tools/ecmascript-lint', 'echo skipped tree audit'],
    ['npm audit --audit-level=moderate --prefix .source-policy/tools/ecmascript-lint', 'echo skipped advisories'],
    ['npm test --prefix .source-policy/tools/ecmascript-lint', 'echo skipped parser tests'],
    ['node --test .source-policy/tools/ecmascript-lint/minimatch-compat.test.mjs', 'echo skipped matcher tests'],
    ['node --test .source-policy/tools/ecmascript-lint/lock-security.test.mjs', 'echo skipped lock tests'],
    ["git rev-parse 'HEAD^{tree}'", 'echo no tree proof'],
    ['actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803', 'actions/checkout@v4'],
    ['permissions:\n  contents: read', 'permissions:\n  contents: write'],
    ['persist-credentials: false', 'persist-credentials: true'],
  ];
  for (const [index, [needle, replacement]] of changes.entries()) {
    assert.ok(workflow.includes(needle), 'missing mutation anchor: ' + index);
    const mutant = workflow.replace(needle, replacement);
    assert.throws(() => admission(mutant), undefined,
      'the mutated source-policy workflow was admitted at case ' + index);
  }
});

test('negative mutation: audit suppression flags, permissive errors and skip-local-test are denied', () => {
  const attacks = [
    '\n      - name: Suppress audit\n        continue-on-error: true\n',
    '\n      - name: Suppress dev audit\n        run: npm audit --omit=dev\n',
    '\n      - name: Ignore audit result\n        run: npm audit --audit-level=moderate || true\n',
    '\n      - name: Skip install audit\n        run: npm audit --no-audit\n',
  ];
  for (const injection of attacks) {
    assert.throws(() => admission(workflow + injection));
  }
  assert.throws(() => admission(workflow.replace(
    'node --test tools/source-policy-rollout.test.mjs',
    'echo local policy test disabled',
  )), /required stage missing/);
});
