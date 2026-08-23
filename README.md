# .github
Organization-wide GitHub defaults and governance for ores-otel


<!-- ore-org-baseline:begin -->
## Organization-wide defaults

This public repository is the canonical source for GitHub-supported community-health fallbacks, organization profile content, contribution guidance, public security/support policy, issue and pull-request templates, and agent-governance declarations for [`ores-otel`](https://github.com/ores-otel).

## Canonical organization links

- GitHub organization: https://github.com/ores-otel
- Public organization defaults: https://github.com/ores-otel/.github
- Canonical Linear project: https://linear.app/denman/project/githubcomores-otel-85e70d77275a
- Fleet tracking issue: https://github.com/ORESoftware/k8s-cluster/issues/1222

## Safety baseline

All Git conflicts must be resolved semantically with full historical, repository-wide, organization-wide, and relevant external-organization context. Automated agents are hard-denied from destructive or history-rewriting operations, including all forms of `git stash`, `git reset`, `git clean`, `git filter-repo`, force pushing, destructive deletion, data or infrastructure teardown, credential revocation, and policy bypass.

## Formal assurance baseline

[`FORMAL_METHODS.md`](FORMAL_METHODS.md) defines the organization assurance
ladder: closed JSON Schemas for wire contracts, algebraic/property checks for
critical pure logic, and explicit state-machine verification plus runtime
refinement for temporal, concurrent, delivery, shutdown, and authorization
behavior in the repository that owns it.

## GitHub inheritance boundary

GitHub can use supported community-health files from a public organization `.github` repository as fallbacks and can render `profile/README.md` on the organization page. `agents.md`, `AGENTS.md`, Copilot instructions, workflows, settings, rulesets, branch protections, permissions, and secrets are not automatically inherited merely because they exist here. Each repository must carry or synchronize compatible local policy and explicitly call reusable workflows where enforcement is required.

Generated managed-policy version: `2026-08-08`.
<!-- ore-org-baseline:end -->

## Reusable source policy lint

`.github/workflows/source-policy-lint.yml` is the cross-organization pre-build lint entry point. Caller repositories must reference a reviewed full commit SHA rather than a mutable branch. The workflow detects tracked source before installing tools and applies the additive `ores-source-policy/v2` rules:

- JavaScript, JSX, TypeScript, and TSX are parsed with ESLint and `@stylistic/eslint-plugin`; omitted semicolons are warnings, while parser failures remain errors. Standalone Ores `@oresoftware/next-loggers` event chains also warn when a level method is not followed by `.send()` (including `.send(true)`). Imported singletons, factories, classes, namespace exports, child loggers, `await`, `void`, and optional chains are recognized. Assigning or returning an event is deliberately allowed because the caller may send it later. Ordinary builders on unrelated objects are ignored. ESLint's normal `ores-fleet/require-send` disable comments provide targeted suppressions.
- Rust is parsed with `syn`. Non-unit functions whose value comes from an implicit tail expression produce one aggregated GitHub warning per run, with at most five concrete file/line/function examples. Explicit `return` statements, unit functions, never-returning functions, macros, and branches whose paths all return explicitly do not warn. Standalone Ores logger chains rooted at recognized `Logger` constructors, factories, child loggers, or conventional logger bindings warn when they omit `.send()` or `.send_with_store(...)`; assigned, returned, macro-wrapped, and unrelated builder expressions are ignored. An intentional auto-send may be suppressed on the same or preceding line with `// ores-source-policy: allow-missing-send`. Tracked Rust source files up to 5 MB are supported so large generated-in-source simulations can still be parsed, while larger files fail with an explicit size diagnostic.
- Warning output is bounded: JavaScript displays at most twenty semicolon examples and five telemetry examples, while Rust emits one aggregate warning per policy with at most five examples. Counts still cover the complete scan. Parse or source-access failures remain errors.

The policy does not rewrite source and does not replace a repository's native ESLint, Clippy, formatting, or package-publication checks.

`source-policy-fleet.json` records the reviewed organization set, the 90-repository/20-organization minimum, and repository-specific delivery exceptions. It is a target-selection contract, not proof of adoption. `source-policy-adoption.json` records per-repository pull-request and merged/default-branch evidence for one exact policy commit. Pass it back to the rollout tool with `--adoption-roster source-policy-adoption.json` when updating an established fleet so repository activity cannot change the target set. Most repositories call the reusable workflow at that immutable commit. Repositories listed in `inlineWorkflowRepositories` prohibit outbound reusable workflows, so the rollout renders equivalent ordinary job steps that still pin and execute the same immutable central implementation.

Validate the implementations locally with:

```bash
npm ci --ignore-scripts --prefix tools/ecmascript-lint
npm test --prefix tools/ecmascript-lint
cargo test --locked --manifest-path tools/rust-explicit-return/Cargo.toml
```
