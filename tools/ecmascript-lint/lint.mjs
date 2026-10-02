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
const MAX_DISPLAYED_SEMICOLON_WARNINGS = 20;
const MAX_DISPLAYED_TELEMETRY_WARNINGS = 5;
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
const LOGGER_EXPORTS = new Set([
  'logger',
  'browserLogger',
  'edgeLogger',
  'cloudflareWorkerLogger',
  'nodeLogger',
  'bunLogger',
  'denoLogger',
]);
const FACTORY_EXPORTS = new Set([
  'createLogger',
  'createBrowserLogger',
  'createEdgeLogger',
  'createCloudflareWorkerLogger',
  'createNodeLogger',
  'createBunLogger',
  'createDenoLogger',
]);
const CLASS_EXPORTS = new Set([
  'BaseLogger',
  'BrowserLogger',
  'EdgeLogger',
  'CloudflareWorkerLogger',
  'NodeLogger',
  'BunLogger',
  'DenoLogger',
]);
const LEVEL_METHODS = new Set(['trace', 'debug', 'info', 'log', 'warn', 'error', 'fatal']);
const TERMINAL_METHODS = new Set(['send']);
const TRACKED_MODULES = new Set(['@oresoftware/next-loggers']);

function hasType(node, ...types) {
  return Boolean(node && types.includes(String(node.type)));
}

function unwrap(node) {
  let current = node;
  while (
    current
    && (
      hasType(
        current,
        'ChainExpression',
        'AwaitExpression',
        'TSAsExpression',
        'TSTypeAssertion',
        'TSNonNullExpression',
      )
      || (current.type === 'UnaryExpression' && current.operator === 'void')
    )
  ) {
    current = current.expression || current.argument;
  }
  return current || undefined;
}

function propertyName(node) {
  if (!hasType(node, 'MemberExpression', 'OptionalMemberExpression')) {
    return undefined;
  }
  const property = node.property;
  if (!property) {
    return undefined;
  }
  if (!node.computed && property.type === 'Identifier') {
    return property.name;
  }
  if (node.computed && property.type === 'Literal' && typeof property.value === 'string') {
    return property.value;
  }
  return undefined;
}

function qualifiedName(node) {
  const current = unwrap(node);
  if (!current) {
    return undefined;
  }
  if (current.type === 'Identifier') {
    return current.name;
  }
  if (current.type === 'ThisExpression') {
    return 'this';
  }
  if (hasType(current, 'MemberExpression', 'OptionalMemberExpression')) {
    const object = qualifiedName(current.object);
    const property = propertyName(current);
    return object && property ? `${object}.${property}` : undefined;
  }
  return undefined;
}

function collectCallChain(node, methods) {
  const current = unwrap(node);
  if (!current) {
    return undefined;
  }
  if (hasType(current, 'CallExpression', 'OptionalCallExpression')) {
    const callee = unwrap(current.callee);
    if (callee && hasType(callee, 'MemberExpression', 'OptionalMemberExpression')) {
      const root = collectCallChain(callee.object, methods);
      const method = propertyName(callee);
      if (method) {
        methods.push(method);
      }
      return root;
    }
    return qualifiedName(callee);
  }
  return qualifiedName(current);
}

function isTrackedModule(source) {
  return typeof source === 'string'
    && [...TRACKED_MODULES].some(
      (moduleName) => source === moduleName || source.startsWith(`${moduleName}/`),
    );
}

export const requireSendRule = {
  meta: {
    type: 'problem',
    docs: {
      description: 'require standalone Ores telemetry events to call send()',
    },
    schema: [],
    messages: {
      missingSend: 'Call .send() on this Ores telemetry event so it is delivered.',
    },
  },

  create(context) {
    const knownLoggers = new Set(['log', 'logger', 'ddlog']);
    const knownFactories = new Set();
    const knownClasses = new Set();

    const isLoggerProducer = (node) => {
      const current = unwrap(node);
      if (!current) {
        return false;
      }
      const directName = qualifiedName(current);
      if (directName && knownLoggers.has(directName)) {
        return true;
      }
      if (current.type === 'NewExpression') {
        const className = qualifiedName(current.callee);
        return Boolean(className && knownClasses.has(className));
      }
      if (hasType(current, 'CallExpression', 'OptionalCallExpression')) {
        const calleeName = qualifiedName(current.callee);
        if (calleeName && knownFactories.has(calleeName)) {
          return true;
        }
        const callee = unwrap(current.callee);
        if (callee && hasType(callee, 'MemberExpression', 'OptionalMemberExpression')) {
          const method = propertyName(callee);
          const owner = qualifiedName(callee.object);
          return method === 'anew' && Boolean(owner && knownLoggers.has(owner));
        }
      }
      return false;
    };

    return {
      ImportDeclaration(node) {
        if (!isTrackedModule(node.source?.value)) {
          return;
        }
        for (const specifier of node.specifiers || []) {
          const localName = specifier.local?.name;
          if (!localName) {
            continue;
          }
          if (specifier.type === 'ImportDefaultSpecifier') {
            knownLoggers.add(localName);
            continue;
          }
          if (specifier.type === 'ImportNamespaceSpecifier') {
            for (const name of LOGGER_EXPORTS) knownLoggers.add(`${localName}.${name}`);
            for (const name of FACTORY_EXPORTS) knownFactories.add(`${localName}.${name}`);
            for (const name of CLASS_EXPORTS) knownClasses.add(`${localName}.${name}`);
            continue;
          }
          const importedName = specifier.imported?.name || specifier.imported?.value;
          if (typeof importedName !== 'string') {
            continue;
          }
          if (LOGGER_EXPORTS.has(importedName)) knownLoggers.add(localName);
          if (FACTORY_EXPORTS.has(importedName)) knownFactories.add(localName);
          if (CLASS_EXPORTS.has(importedName)) knownClasses.add(localName);
        }
      },

      VariableDeclarator(node) {
        if (node.id?.type === 'Identifier' && node.id.name && isLoggerProducer(node.init)) {
          knownLoggers.add(node.id.name);
        }
      },

      AssignmentExpression(node) {
        const assignedName = qualifiedName(node.left);
        if (assignedName && isLoggerProducer(node.right)) {
          knownLoggers.add(assignedName);
        }
      },

      ExpressionStatement(node) {
        const methods = [];
        const root = collectCallChain(node.expression, methods);
        if (!root || !knownLoggers.has(root)) {
          return;
        }
        const levelIndex = methods.findIndex((method) => LEVEL_METHODS.has(method));
        if (levelIndex < 0) {
          return;
        }
        if (methods.slice(levelIndex + 1).some((method) => TERMINAL_METHODS.has(method))) {
          return;
        }
        context.report({ node, messageId: 'missingSend' });
      },
    };
  },
};

const telemetryPlugin = {
  meta: { name: '@ores-otel/fleet-source-policy', version: '0.2.0' },
  rules: { 'require-send': requireSendRule },
};

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
          'ores-fleet': telemetryPlugin,
          stylistic,
        },
        rules: {
          'ores-fleet/require-send': 'warn',
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
        } else if (message.ruleId === 'ores-fleet/require-send') {
          counts.telemetryMissingSends += 1;
        }
      }
      return counts;
    },
    { errors: 0, warnings: 0, missingSemicolons: 0, telemetryMissingSends: 0 },
  );
}

function boundedResults(results) {
  let semicolonWarnings = 0;
  let telemetryWarnings = 0;

  return results
    .map((result) => {
      const messages = result.messages.filter((message) => {
        if (message.severity === 2) {
          return true;
        }
        if (message.ruleId === 'stylistic/semi') {
          semicolonWarnings += 1;
          return semicolonWarnings <= MAX_DISPLAYED_SEMICOLON_WARNINGS;
        }
        if (message.ruleId === 'ores-fleet/require-send') {
          telemetryWarnings += 1;
          return telemetryWarnings <= MAX_DISPLAYED_TELEMETRY_WARNINGS;
        }
        return true;
      });
      return {
        ...result,
        errorCount: messages.filter((message) => message.severity === 2).length,
        fatalErrorCount: messages.filter((message) => message.fatal).length,
        messages,
        warningCount: messages.filter((message) => message.severity === 1).length,
      };
    })
    .filter((result) => result.messages.length > 0);
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
      `- Ores telemetry events missing .send(): ${counts.telemetryMissingSends}`,
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
      counts: {
        errors: 0,
        warnings: 0,
        missingSemicolons: 0,
        telemetryMissingSends: 0,
      },
    });
    return 0;
  }

  const linter = createLinter(root);
  const results = await linter.lintFiles(sourcePaths);
  const formatter = await linter.loadFormatter('stylish');
  const formatted = await formatter.format(boundedResults(results));
  if (formatted) {
    process.stdout.write(formatted);
  }

  const counts = countMessages(results);
  console.log(
    `ECMAScript source policy: checked ${sourcePaths.length} tracked source file(s); `
      + `${counts.missingSemicolons} missing-semicolon warning(s); `
      + `${counts.telemetryMissingSends} Ores telemetry event(s) missing .send(); `
      + `${counts.errors} error(s).`,
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
