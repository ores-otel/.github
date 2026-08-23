# Governance

## Canonical organization links

- GitHub organization: https://github.com/ores-otel
- Public organization defaults: https://github.com/ores-otel/.github
- Canonical Linear project: https://linear.app/denman/project/githubcomores-otel-85e70d77275a
- Fleet tracking issue: https://github.com/ORESoftware/k8s-cluster/issues/1222

Organization owners are accountable for repository creation, visibility, access, archival, public defaults, and cross-repository governance. Repository maintainers own implementation quality and releases within published contracts. Material architecture decisions must be documented in the owning repository and reflected in interfaces, tests, deployment ownership, and observability expectations.

Critical contracts, accounting laws, and state-machine behavior follow the
organization [`FORMAL_METHODS.md`](FORMAL_METHODS.md) assurance ladder. Models
live with the authoritative behavior, must identify their finite proof boundary,
and supplement rather than replace exact-revision runtime and deployment
evidence.

Resolve conflicts semantically with complete historical and cross-repository context. Automated agents must not execute destructive or history-rewriting operations.
