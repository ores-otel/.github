# Contract authority

`ores-platform/v1/schema.json` is the canonical portfolio wire contract.
`shared-auth-admin/v1/schema.json` is the canonical Shared Auth administration contract.
Bindings must preserve:

1. tenant and audience boundaries;
2. fail-closed assurance and authentication-method values;
3. bounded delegation depth;
4. no raw biometric material;
5. no token or secret values in errors, logs, or security events;
6. inactive introspection responses by default when state is unknown.

Shared Auth directory grants additionally require:

1. the wrapped `DirectoryAdminGrantSet` discriminator and payload, never a loose object;
2. exact audience introspection at AAL2 or AAL3 and a required token/session `expiresAt`;
3. canonical UUIDs for grant, organization, and optional project identifiers;
4. exact non-wildcard directory scopes and an explicit `directory_admin` role;
5. no flat organization/project/scope claims outside `directoryGrants`;
6. no raw email field or cross-organization fallback.

Shared Auth global revocation additionally requires:

1. a service-authenticated exchange whose subject/access tokens are write-only, never fixture or
   log material, and bound to the exact `shared-auth-web-server` audience and singular global
   revocation scope;
2. immutable principal IDs; email is a transient operator search input and becomes a keyed
   digest before it enters the canonical contract;
3. explicit ambiguity handling and a short-lived server-bound principal-selection handoff;
4. provider tenant plus internal opaque identity handles, never raw provider credentials;
5. preview-before-execute blast-radius reporting with nullable unknown counts, explicit inventory
   status, exact unknown-field names, and explicit revocation scopes;
6. fresh phishing-resistant AAL2-or-higher WebAuthn step-up represented to the committing client
   only by a short-lived, one-use server-issued commit-authorization handle;
7. an auth-epoch/not-before fence committed before provider fan-out;
8. idempotent durable jobs with honest partial state and per-target bounded retry metadata,
   present only for scheduled retries and absent from terminal target results;
9. redacted audit correlation with no raw tokens, email addresses, session IDs, provider
   response bodies, or biometric material.

Changes require a versioned schema path and compatibility notes. Do not mutate v1 semantics
in place after a stable release.

`shared-auth/v1/schema.json` is the canonical cross-organization identity domain contract.
It covers organizations, projects, safe user projections, memberships, roles and bindings,
safe session/factor projections, audit events, and revocation by normalized email. The
revocation request carries the address as a write-only value; implementations normalize it
in memory, derive a keyed lookup HMAC, and discard it. The result cannot echo the address or
identify an organization for which the actor lacks `sessions.revoke`.

The schema's `Factor` projection deliberately has no verifier, private-key, biometric image,
or biometric-template field. Platform face/fingerprint/thumbprint checks are local WebAuthn
user-verification verdicts. SSH/OpenPGP keys remain with the credential authority; Shared
Auth stores an external-reference digest or public fingerprint only.

The four primary bindings are explicitly catalogued in
`shared-auth/v1/bindings.json`. They are hand-maintained because the foundational packages
remain dependency-free; `scripts/check_contracts.py` fails CI if a binding or required domain
type disappears. JSON Schema remains authoritative when a language type and wire rule differ.
in place after a stable release. The still-draft Shared Auth revocation control-plane definitions
preserve all existing v1 read-projection semantics.
