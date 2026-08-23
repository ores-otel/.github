import assert from 'node:assert/strict';
import { mkdtemp } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { createLinter, shouldSkip } from './lint.mjs';

async function lintText(source, filePath) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'ores-fleet-eslint-'));
  const linter = createLinter(root);
  const [result] = await linter.lintText(source, { filePath: path.join(root, filePath) });
  return result.messages;
}

test('missing semicolons are warnings', async () => {
  const messages = await lintText(
    'const answer: number = 42\nexport { answer }\n',
    'src/answer.ts',
  );

  assert.equal(messages.length, 2);
  assert.equal(messages.every((message) => message.ruleId === 'stylistic/semi'), true);
  assert.equal(messages.every((message) => message.severity === 1), true);
});

test('explicit semicolons pass', async () => {
  const messages = await lintText(
    'const answer = 42;\nexport { answer };\n',
    'src/answer.mjs',
  );

  assert.deepEqual(messages, []);
});

test('TypeScript and JSX syntax parse without project configuration', async () => {
  const messages = await lintText(
    'type Props = { label: string };\nexport const Button = ({ label }: Props) => <button>{label}</button>;\n',
    'src/button.tsx',
  );

  assert.deepEqual(messages, []);
});

test('generated and dependency trees are excluded', () => {
  assert.equal(shouldSkip('src/index.ts'), false);
  assert.equal(shouldSkip('dist/index.js'), true);
  assert.equal(shouldSkip('vendor/sdk/client.ts'), true);
  assert.equal(shouldSkip('web/_astro/page.hash.js'), true);
  assert.equal(shouldSkip('node_modules/pkg/index.js'), true);
});
