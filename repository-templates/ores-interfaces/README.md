# ores-interfaces

Canonical, language-neutral interfaces shared across OreSoftware organizations.

The repository is deliberately **contract-first**. `contracts/ores-platform/v1/schema.json`
is the authority; language folders are reviewed bindings for services and clients. Product
repositories may extend these types in their own namespaces, but must not weaken tenant,
audience, assurance, retention, or redaction semantics.

## Layout

- `contracts/` — JSON Schema 2020-12 contracts and security invariants.
- `languages/rust` — zero-dependency Rust data types.
- `languages/typescript` — runtime constants plus TypeScript declarations.
- `languages/go` — Go structs and enums.
- `languages/python` — Python enums and dataclasses.
- `languages/dart` — Dart enums and immutable value types.
- `languages/java` — Java 17 records and enums.
- `languages/swift` — Swift `Codable` value types.
- `scripts/check_contracts.py` — offline drift and secret-safety checks.

## Authentication boundaries

`platform_biometric` means a platform authenticator performed local user verification
(WebAuthn/passkey). Raw face images, face templates, fingerprint images, fingerprint
templates, or modality-specific secrets are never part of these contracts. OpenPGP is a
provenance mechanism unless an application explicitly adopts a separately reviewed auth
profile. Kerberos and SSH integrations must exchange short-lived, audience-bound tokens;
they do not grant roles directly from PAC groups, Unix principals, or key comments.

## Zed package

```sh
zed add ores-otel/ores-interfaces@^0.1
zed install --frozen
```

The root `.zpkg.toml` publishes one coordinated package with per-language targets.
