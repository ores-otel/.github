# Contributing to ores-otel

## Canonical organization links

- GitHub organization: https://github.com/ores-otel
- Public organization defaults: https://github.com/ores-otel/.github
- Canonical Linear project: https://linear.app/denman/project/githubcomores-otel-85e70d77275a
- Fleet tracking issue: https://github.com/ORESoftware/k8s-cluster/issues/1222

Read the target repository's local `agents.md`, architecture, contracts, tests, and deployment documentation before editing. Use a focused branch and pull request, link the relevant Linear work, preserve unrelated changes, and document validation, compatibility, migration, security, and operational effects.

Complete the pull request's formal-methods assessment. Follow
[`FORMAL_METHODS.md`](FORMAL_METHODS.md) for public schemas, algebraic security
properties, and critical state-machine or concurrency changes.

Resolve conflicts semantically with complete historical and cross-repository context. Automated agents must not execute destructive or history-rewriting operations.

## Rust-first scripts and automation

**No new Python scripts.** For first-party CI/build/test tooling, migrations, code generation, releases, deployment helpers, security audits and repository maintenance, use Rust CLIs or `cargo xtask` rather than Python. Keep shell/YAML wrappers thin.

Inventory existing Python scripts as migration debt and document their callers. Before retiring any Python entry point, implement and verify a Rust replacement with equivalent flags, output formats, exit statuses, failure and security semantics, and supported platform behavior; then update tests, CI, docs and hooks. Require meaningful positive, negative and end-to-end execution on the exact head commit. A docs PR is not evidence of runtime migration.

**Python application code can remain in explicitly reviewed, narrowly justified cases** with an owner, scope and rationale. App-specific tests may be included; CI helpers and ordinary automation cannot be justified merely by calling them app code.

Document reproducible Cargo build/run instructions and relevant `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test` and end-to-end smoke checks. Never claim source-level execution on the basis of an unexecuted test or source-free canary.

Canonical organization `.github` contributor guidance is not automatically propagated as custom `AGENTS.md` or CI enforcement to every repository. Synchronize and enable local instructions/checks explicitly.

