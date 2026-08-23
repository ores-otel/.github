# ores-interfaces

Canonical, language-neutral interfaces shared across OreSoftware organizations.

The repository is deliberately **contract-first**. `contracts/ores-platform/v1/schema.json`
is the authority for portfolio-wide identity, request, error, capability, and security-event
shapes. `contracts/shared-auth-admin/v1/schema.json` adds the read-only organization dashboard
projection used by Shared Auth and the additive global session-revocation workflow described
below. It also defines the AAL2+ `DirectoryAdminGrantSet` consumed by the administrative web
server. Product repositories may extend these types in their own namespaces, but must not
weaken tenant, audience, assurance, retention, pagination, or redaction semantics.

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
`DirectoryAdminGrantSet` is a discriminator-bound envelope payload returned only after active,
exact-audience introspection at AAL2 or AAL3. Each nested `DirectoryAdminGrant` carries one
canonical organization UUID, optional non-empty project UUIDs, exact non-wildcard scopes, and
an explicit `directory_admin` role. The set carries the introspected token/session `expiresAt`;
the UI must not outlive that bound. Organization/project authority never appears as a flat
claim on the grant set, raw email is prohibited, and cross-organization fallback is false.

## Safe global session revocation

The revocation workflow is deliberately separate from the existing read projections:

1. After exact directory-grant authorization, `AdminRevocationTokenExchangeRequest` performs a
   service-authenticated, exact-audience exchange for the singular
   `shared-auth:sessions:revoke:global` scope. The subject and returned access token fields are
   write-only contract material: they never enter examples, fixtures, logs, persistence, errors,
   or diagnostics. The result is `Bearer`, expires within five minutes, and fixes both audience
   and authorized party to `shared-auth-web-server`; revocation routes reverify all authority.
2. A trusted edge accepts an operator-entered email only long enough to normalize it and
   compute a domain-separated keyed digest. Canonical contracts, examples, jobs, and audit
   events never contain the raw address.
3. `PrincipalSearchResult` can return no match, one match, or multiple candidates. A candidate
   carries an immutable `principalId` plus provider tenant and internal opaque identity handles;
   an ambiguous result requires explicit principal selection.
4. `PrincipalSelectionRequest` confirms one candidate from the stored lookup. Its result returns
   a short-lived opaque `selectionId`; `GlobalRevocationPreviewRequest` carries only that handle
   and the exact scopes, never a principal or email field.
5. `GlobalRevocationPreview` freezes the selected scopes and displays the provider, organization,
   project, session, grant, credential, and device-session blast radius before execution. Each
   count is either an authoritative integer (including zero) or `null`; `inventoryStatus` and
   exact `unknownFields` make partial or unavailable inventory explicit.
6. A fresh phishing-resistant WebAuthn step-up at AAL2 or AAL3 produces a short-lived, one-use
   `GlobalRevocationCommitAuthorization`. It binds the preview, immutable principal, exact scope
   set, verified actor, and optional dual-control decision. Its expiry cannot exceed either the
   preview expiry or step-up freshness limit. The browser receives an opaque handle and cannot
   assert actor, session, evidence, assurance, or freshness fields in `GlobalRevocationRequest`.
   Reusing an idempotency key or commit authorization with different resolved state is a conflict,
   not a second operation.
7. Creating `GlobalRevocationOperation` atomically increments the principal auth epoch and
   records a `notBefore` fence before provider fan-out starts. Shared Auth authorizers reject
   older tokens even when a provider is unavailable or a provider JWT remains valid until its
   expiry.
8. Each provider target reports a redacted machine result, retryability, attempts, and bounded
   retry timing. `retry_scheduled` requires both `nextAttemptAt` and a positive
   `retryAfterSeconds`; terminal targets (`succeeded`, `failed`, `skipped`, or `unsupported`)
   carry neither field. A job can truthfully finish `partial`; it must never report success
   while a mandatory target failed or is unsupported.

The operation never carries raw provider tokens, raw session identifiers, raw email addresses,
provider response bodies, free-form provider errors, face data, or fingerprint data. Provider
identity handles and audit identifiers are internal opaque values or keyed digests. Idempotency
keys are write-only and only their keyed digests appear in responses and audit records.

### Compatibility

The dashboard query, response, user, session, role, organization, project, and capability
definitions retain their v1 fields and semantics. Directory grants and the still-draft revocation
control-plane contracts do not weaken those projections. Consumers that do not implement them can continue using the
read projections; exhaustive discriminator consumers should negotiate or reject unknown
contract names rather than silently interpreting them.

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
