import { execFileSync } from 'node:child_process';
import { appendFile, lstat } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

import stylistic from '@stylistic/eslint-plugin';
import * as typescriptParser from '@typescript-eslint/parser';
import { ESLint } from 'eslint';

const SOURCE_EXTENSION = /\.(?:cjs|mjs|js|jsx|ts|tsx)$/i;
const MAX_SOURCE_BYTES = 1_000_000;
const SKIPPED_COMPONENTS = new Set([
  '.cache',
  '.git',
  '.next',
  '.nuxt',
  '_astro',
  'build',
  'coverage',
  'dist',
  'fixtures',
  'generated',
  'node_modules',
  'out',
  'target',
  'third_party',
  'vendor',
]);

export function shouldSkip(relativePath) {
  return relativePath
    .split(/[\\/]/u)
    .some((component) => SKIPPED_COMPONENTS.has(component));
}

export function trackedEcmaScriptPaths(root) {
  const output = execFileSync('git', ['-C', root, 'ls-files', '-z'], {
    encoding: 'buffer',
    maxBuffer: 128 * 1024 * 1024,
  });

  return output
    .toString('utf8')
    .split('\0')
    .filter(Boolean)
    .filter((relativePath) => SOURCE_EXTENSION.test(relativePath))
    .filter((relativePath) => !shouldSkip(relativePath))
    .sort();
}

async function sourceSizedPaths(root, relativePaths) {
  const accepted = [];

  for (const relativePath of relativePaths) {
    const metadata = await lstat(path.join(root, relativePath));
    if (!metadata.isFile()) {
      throw new Error(`tracked ECMAScript source is not a regular file: ${relativePath}`);
    }
    if (metadata.size > MAX_SOURCE_BYTES) {
      throw new Error(
        `tracked ECMAScript source exceeds ${MAX_SOURCE_BYTES} bytes: ${relativePath}`,
      );
    }
    accepted.push(relativePath);
  }

  return accepted;
}

export function createLinter(root) {
  return new ESLint({
    cwd: root,
    overrideConfigFile: true,
    overrideConfig: [
      {
        name: 'ores-fleet/source-semicolon-policy',
        files: ['**/*.{cjs,mjs,js,jsx,ts,tsx}'],
        languageOptions: {
          parser: typescriptParser,
          parserOptions: {
            ecmaFeatures: { jsx: true },
            ecmaVersion: 'latest',
            sourceType: 'unambiguous',
          },
        },
        plugins: {
          stylistic,
        },
        rules: {
          'stylistic/semi': ['warn', 'always'],
        },
      },
    ],
  });
}

function countMessages(results) {
  return results.reduce(
    (counts, result) => {
      for (const message of result.messages) {
        if (message.severity === 2) {
          counts.errors += 1;
        } else if (message.severity === 1) {
          counts.warnings += 1;
        }
        if (message.ruleId === 'stylistic/semi') {
          counts.missingSemicolons += 1;
        }
      }
      return counts;
    },
    { errors: 0, warnings: 0, missingSemicolons: 0 },
  );
}

async function writeStepSummary({ files, counts }) {
  const summaryPath = process.env.GITHUB_STEP_SUMMARY;
  if (!summaryPath) {
    return;
  }

  await appendFile(
    summaryPath,
    [
      '### ECMAScript source policy',
      '',
      `- Tracked source files checked: ${files}`,
      `- Missing-semicolon warnings: ${counts.missingSemicolons}`,
      `- Other parser/lint errors: ${counts.errors}`,
      '',
    ].join('\n'),
  );
}

export async function run(root) {
  const trackedPaths = trackedEcmaScriptPaths(root);
  const sourcePaths = await sourceSizedPaths(root, trackedPaths);

  if (sourcePaths.length === 0) {
    console.log('ECMAScript source policy: no tracked JS/TS source files found.');
    await writeStepSummary({
      files: 0,
      counts: { errors: 0, warnings: 0, missingSemicolons: 0 },
    });
    return 0;
  }

  const linter = createLinter(root);
  const results = await linter.lintFiles(sourcePaths);
  const formatter = await linter.loadFormatter('stylish');
  const formatted = await formatter.format(results);
  if (formatted) {
    process.stdout.write(formatted);
  }

  const counts = countMessages(results);
  console.log(
    `ECMAScript source policy: checked ${sourcePaths.length} tracked source file(s); `
      + `${counts.missingSemicolons} missing-semicolon warning(s); ${counts.errors} error(s).`,
  );
  await writeStepSummary({ files: sourcePaths.length, counts });
  return counts.errors === 0 ? 0 : 1;
}

async function main() {
  const root = path.resolve(process.argv[2] ?? process.cwd());
  try {
    process.exitCode = await run(root);
  } catch (error) {
    console.error(`ECMAScript source policy failed: ${error?.stack ?? error}`);
    process.exitCode = 1;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
