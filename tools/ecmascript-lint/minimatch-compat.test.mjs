import test from "node:test";
import assert from "node:assert/strict";
import { Minimatch, minimatch } from "minimatch";

test("minimatch 11 retains normal source-file glob matching required by ESLint consumers", () => {
  const valid = [
    ["src/index.mjs", "**/*.mjs"],
    ["tools/ecmascript-lint/lint.test.mjs", "**/*.test.mjs"],
    ["src/deep/view.tsx", "**/*.tsx"],
    ["src/README.md", "**/*.md"],
    ["foo/bar/file.js", "foo/**/file.js"],
  ];
  for (const [file, pattern] of valid) {
    assert.equal(minimatch(file, pattern, { dot: false }), true, file + " " + pattern);
    assert.equal(new Minimatch(pattern, { optimizationLevel: 2 }).match(file),
      true, "optimized: " + file + " " + pattern);
  }
  const invalid = [
    ["src/index.mjs", "**/*.ts"],
    ["src/secret.env", "**/*.js"],
    [".secret/hidden.js", "**/*.js"],
    ["src/main.tsx", "**/*.mjs"],
  ];
  for (const [file, pattern] of invalid) {
    assert.equal(minimatch(file, pattern, { dot: false }), false, file + " " + pattern);
  }
});

test("dotfiles remain hidden by default; explicit dot option admits only expected files", () => {
  const matcher = new Minimatch("**/*.js", { dot: true, optimizationLevel: 2 });
  assert.equal(matcher.match(".private/index.js"), true);
  assert.equal(matcher.match("public/index.js"), true);
  assert.equal(matcher.match(".private/index.ts"), false);
  assert.equal(minimatch(".private/index.js", "**/*.js", { dot: false }), false);
});
