# Formal methods policy

The `ores-otel` organization uses the lightest verification technique that can
express the risk. JSON Schema is mandatory for stable wire contracts, but it is
not treated as proof of temporal behavior, concurrency, authorization, or
eventual delivery.

## Assurance ladder

### Level 0: structural contracts

Use closed JSON Schema Draft 2020-12 documents, positive fixtures, adversarial
negative fixtures, stable discriminators, and compatibility checks for every
public wire format. Generated bindings must refine the canonical schema; a
language type definition is not an independent contract authority.

### Level 1: algebraic and property checks

Pure security or accounting logic must state and execute its laws. Typical
properties include idempotence, monotonicity, conservation, noninterference,
round trips, bounds, and fail-closed defaults. Generate a finite adversarial
domain deterministically and run the equivalent property suite in every
material implementation language.

Examples:

- redaction is idempotent and sensitive-value noninterfering;
- serialization never reveals a secret wrapper;
- accepted/dropped/queued/in-flight counters conserve all attempted work;
- identifier and payload limits hold at both boundaries.

### Level 2: explicit state-machine verification

A checked state-machine model is required when a change introduces or changes:

- retry, queue, backpressure, batching, outbox, delivery, or acknowledgement
  lifecycles;
- graceful/forced shutdown, flush, startup, readiness, leader, lease, or lock
  transitions;
- session, token, revocation, factor, delegation, authorization, or account
  lifecycle behavior in the repository that owns that authority;
- cross-thread/task/process coordination or idempotent distributed operations;
- any other security- or availability-critical transition graph.

Use TLA+/PlusCal by default for concurrent or temporal behavior. Another tool
is acceptable when it checks the same explicit transition relation and its
safety/liveness properties. The model must declare:

1. states, events/actions, initial state, and transition guards;
2. resource bounds and accounting variables;
3. safety invariants and terminal-state rules;
4. liveness properties and fairness assumptions where progress is claimed;
5. the finite model bounds and what remains outside the proof;
6. a mapping from modeled actions to production source and tests.

At least one executable finite-state/refinement check must be independent of
the temporal model. Polyglot implementations must consume one versioned vector
corpus or demonstrate the equivalent relation in each language. Rust should
also use exhaustive/property checks and Loom or an equivalent concurrency
explorer when shared-memory interleavings are material.

### Level 3: runtime and fault evidence

Formal checks complement rather than replace real-runtime evidence. Retain
concurrency tests, fault injection, network failures, timeouts, crash/restart,
packed-consumer tests, and end-to-end checks at exact revisions. A model cannot
prove the scheduler, network, storage engine, collector, or deployment matches
its abstraction.

## Ownership

Put the model beside the authoritative behavior:

- `ores.otel.log` owns telemetry buffering, delivery, flush, and shutdown;
- `ores-mcp-server-core-libs.rs` owns its MCP lifecycle;
- `ores-interfaces` owns wire schemas, not authentication or product-policy
  transitions;
- Shared Auth session/revocation models belong with the Shared Auth server
  authority; product membership and resource authorization remain in the
  owning product repository.

Do not copy a behavioral model into an interface, SDK, MCP diagnostics, or
downstream consumer merely because that repository has convenient tooling.
Consumers should refine versioned contracts from the owner.

## CI and supply-chain requirements

- Pin model-checker/action inputs to reviewed immutable revisions. Downloaded
  tools must use HTTPS and a checked cryptographic digest.
- Keep model inputs, counterexamples, and fixtures synthetic and credential
  free. Never serialize production payloads or identity material into traces.
- Run formal checks on pull requests and protected default-branch pushes when
  the model, mapped production source, vectors, or workflow changes.
- A counterexample is a failing test. Fix the implementation or correct the
  reviewed abstraction; never weaken an invariant merely to make CI pass.
- Preserve exact state/transition counts and tool versions in CI evidence when
  useful, while documenting that fingerprint collision estimates and bounded
  exploration are not unbounded mathematical proof.

## Pull-request assessment

Every pull request must say one of the following:

- `Formal methods: not applicable` with a short ownership/risk reason;
- `Formal methods: existing model unchanged` with the model and refinement
  checks named; or
- `Formal methods: updated` with invariants, bounds, counterexamples found,
  runtime mapping, and exact CI evidence.

An exception for applicable critical logic requires explicit maintainer review,
a tracked follow-up, a conservative fail-closed implementation, and a bounded
roll-forward plan. Schedule pressure alone is not an exception.
