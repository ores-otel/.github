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

test('unfinished Ores telemetry chains are warn-only findings', async () => {
  const messages = await lintText(
    [
      "import nextLoggers, { createNodeLogger as makeLogger } from '@oresoftware/next-loggers/node';",
      'const audit = makeLogger();',
      "nextLoggers.info('missing');",
      "audit.error('also missing').addFields({ requestId: 'r1' });",
      '',
    ].join('\n'),
    'src/telemetry.ts',
  );
  const telemetryMessages = messages.filter(
    (message) => message.ruleId === 'ores-fleet/require-send',
  );

  assert.equal(telemetryMessages.length, 2);
  assert.equal(telemetryMessages.every((message) => message.severity === 1), true);
  assert.equal(telemetryMessages.every((message) => /\.send\(\)/u.test(message.message)), true);
});

test('delivered, deferred, and unrelated builder chains do not warn', async () => {
  const messages = await lintText(
    [
      "import { createLogger } from '@oresoftware/next-loggers';",
      'const logger = createLogger();',
      "logger.info('sent').send();",
      "logger.warn('stored').send(true);",
      "const deferred = logger.error('sent later');",
      'void deferred;',
      "query.info('ordinary builder').where({ active: true });",
      'function buildEvent() {',
      "  return logger.debug('returned to caller');",
      '}',
      'void buildEvent;',
      '',
    ].join('\n'),
    'src/builders.ts',
  );

  assert.equal(
    messages.some((message) => message.ruleId === 'ores-fleet/require-send'),
    false,
  );
});

test('telemetry rule supports namespace imports, child loggers, wrappers, and suppressions', async () => {
  const messages = await lintText(
    [
      "import * as logging from '@oresoftware/next-loggers';",
      'const parent = logging.createLogger();',
      "const child = parent.anew({ appName: 'child' });",
      "await child.info('sent').send();",
      "void parent.warn('missing');",
      '// eslint-disable-next-line ores-fleet/require-send',
      "parent.error('intentionally auto-sent');",
      '',
    ].join('\n'),
    'src/wrappers.mjs',
  );
  const telemetryMessages = messages.filter(
    (message) => message.ruleId === 'ores-fleet/require-send',
  );

  assert.equal(telemetryMessages.length, 1);
  assert.match(telemetryMessages[0].message, /\.send\(\)/u);
});
