# Contract authority

`ores-platform/v1/schema.json` is the canonical wire contract. Bindings must preserve:

1. tenant and audience boundaries;
2. fail-closed assurance and authentication-method values;
3. bounded delegation depth;
4. no raw biometric material;
5. no token or secret values in errors, logs, or security events;
6. inactive introspection responses by default when state is unknown.

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
