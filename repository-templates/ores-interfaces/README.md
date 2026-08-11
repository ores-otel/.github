# ores-interfaces

Canonical, language-neutral interfaces shared across OreSoftware organizations.

The repository is deliberately **contract-first**. `contracts/ores-platform/v1/schema.json`
is the authority for portfolio-wide identity, request, error, capability, and security-event
shapes. `contracts/shared-auth-admin/v1/schema.json` adds the read-only organization dashboard
projection used by Shared Auth. Product repositories may extend these types in their own
namespaces, but must not weaken tenant, audience, assurance, retention, pagination, or
redaction semantics.

## Layout

- `contracts/ores-platform/v1` — portfolio-wide JSON Schema 2020-12 contracts.
- `contracts/shared-auth-admin/v1` — organization dropdown, project scope, users, sessions,
  role bindings, capability truth, and dashboard redaction contracts.
- `contracts/shared-auth/v1` — canonical organizations/projects/users/memberships/roles,
  sessions/factors/audit projections, plus authorized idempotent cross-org revocation.
- `languages/rust` — zero-dependency Rust data types.
- `languages/typescript` — runtime constants plus TypeScript declarations.
- `languages/go` — Go structs and enums.
- `languages/python` — Python enums and dataclasses.
- `languages/dart` — Dart enums and immutable value types.
- `languages/java` — Java 17 records and enums.
- `languages/swift` — Swift `Codable` value types.
- `scripts/check_contracts.py` — offline drift, capability-truth, redaction, and secret-safety
  checks.

## Shared Auth administration boundary

The dashboard contract is intentionally read-only and organization-scoped:

- every request selects an exact organization; there is no cross-organization fallback;
- role bindings always carry an explicit organization/project/repository scope;
- session IDs, bearer tokens, raw IP addresses, and biometric material never enter the view;
- SSH and Kerberos capability records require online introspection and cannot exceed AAL1;
- OpenPGP is provenance-only and cannot mint a Shared Auth token;
- face/fingerprint/thumbprint language means local platform-authenticator user verification
  behind WebAuthn, not collection or retention of images or templates;
- non-implemented capabilities must advertise `productionEnabled: false`.

## Cross-organization session revocation

`RevokeSessionsByEmailRequest` is a command to the trusted Shared Auth server, not a direct
database operation. The server must normalize the ASCII address, derive a keyed HMAC for
lookup, and discard the address before logging or persistence. For every candidate
organization, it verifies the actor's `sessions.revoke` permission independently. Results
list authorized organizations only and expose a count—not identities—for unprocessed scope.

Idempotency is scoped to the verified actor plus `idempotencyKey`. Reusing that key with the
same canonical request digest replays the sanitized result; using it with a different digest
is a conflict. Partial failure is per organization, and each authorized attempt emits an
`AuditEvent` through the injected `ores.otel.log` adapter.

## Authentication boundaries

`platform_biometric` means a platform authenticator performed local user verification
(WebAuthn/passkey). Raw face images, face templates, fingerprint images, fingerprint
templates, or modality-specific secrets are never part of these contracts. OpenPGP is a
provenance mechanism. Kerberos and SSH integrations use bounded, audience-specific,
revocation-aware credential exchanges; PAC groups, Unix principals, and key comments never
grant application roles directly.

## Zed package

```sh
zed add ores-otel/ores-interfaces@^0.1
zed install
```

After the first registry-backed resolution creates and commits `.zpkg.lock`, CI and
repeatable deployments should use:

```sh
zed install --frozen
```

The root `.zpkg.toml` publishes one coordinated package with per-language targets. A
placeholder lock is intentionally not committed because it would not prove artifact
provenance or direct dependency coverage.
