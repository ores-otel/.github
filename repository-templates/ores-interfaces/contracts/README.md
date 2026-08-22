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
