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

`.github/workflows/source-policy-lint.yml` is the cross-organization pre-build lint entry point. Caller repositories must reference a reviewed full commit SHA rather than a mutable branch. The workflow detects tracked source before installing tools and applies two additive policies:

- JavaScript, JSX, TypeScript, and TSX are parsed with ESLint and `@stylistic/eslint-plugin`; omitted semicolons are warnings, while parser failures remain errors. Dependency, generated, coverage, build, and vendored trees are excluded.
- Rust is parsed with `syn`. Non-unit functions whose value comes from an implicit tail expression produce one aggregated GitHub warning per run, with at most five concrete file/line/function examples. Explicit `return` statements, unit functions, never-returning functions, and branches whose paths all return explicitly do not warn.

The policy does not rewrite source and does not replace a repository's native ESLint, Clippy, formatting, or package-publication checks. Validate the implementations locally with:

```bash
npm ci --ignore-scripts --prefix tools/ecmascript-lint
npm test --prefix tools/ecmascript-lint
cargo test --locked --manifest-path tools/rust-explicit-return/Cargo.toml
```
