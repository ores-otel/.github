export const AuthMethod = Object.freeze({
  JWT: "jwt", OIDC: "oidc", WEBAUTHN: "webauthn", TOTP: "totp",
  KERBEROS: "kerberos", SSH: "ssh", OPENPGP: "openpgp",
  PLATFORM_BIOMETRIC: "platform_biometric", RECOVERY: "recovery"
});
export const AssuranceLevel = Object.freeze({AAL0: "aal0", AAL1: "aal1", AAL2: "aal2", AAL3: "aal3"});
export const DirectoryAdminScope = Object.freeze({
  DASHBOARD_READ: "directory.dashboard.read",
  USERS_READ: "directory.users.read",
  SESSIONS_READ: "directory.sessions.read",
  ROLES_READ: "directory.roles.read",
  REVOCATIONS_READ: "directory.revocations.read",
  REVOCATIONS_EXECUTE: "directory.revocations.execute"
});
export const DirectoryAdminRole = Object.freeze({
  DIRECTORY_ADMIN: "directory_admin",
  DIRECTORY_SECURITY_OPERATOR: "directory_security_operator",
  DIRECTORY_AUDITOR: "directory_auditor"
});
export const PrincipalSearchState = Object.freeze({NO_MATCH: "no_match", UNIQUE: "unique", AMBIGUOUS: "ambiguous"});
export const InventoryStatus = Object.freeze({COMPLETE: "complete", PARTIAL: "partial", UNAVAILABLE: "unavailable"});
export const RevocationScope = Object.freeze({
  INTERACTIVE_SESSIONS: "interactive_sessions",
  REFRESH_TOKEN_FAMILIES: "refresh_token_families",
  OFFLINE_GRANTS: "offline_grants",
  DOWNSTREAM_SESSIONS: "downstream_sessions",
  IMPERSONATION_SESSIONS: "impersonation_sessions",
  USER_API_CREDENTIALS: "user_api_credentials",
  REGISTERED_DEVICE_SESSIONS: "registered_device_sessions"
});
export const RevocationJobState = Object.freeze({QUEUED: "queued", RUNNING: "running", PARTIAL: "partial", SUCCEEDED: "succeeded", FAILED: "failed", CANCELLED: "cancelled"});
export const RevocationTargetState = Object.freeze({PENDING: "pending", RUNNING: "running", RETRY_SCHEDULED: "retry_scheduled", SUCCEEDED: "succeeded", FAILED: "failed", SKIPPED: "skipped", UNSUPPORTED: "unsupported"});
export function isSafePlatformBiometricProof(value) {
  return value?.verifiedByPlatformAuthenticator === true
    && value?.userVerification === "required"
    && value?.rawBiometricMaterialPresent === false;
}
export function isSufficientRevocationStepUp(value) {
  return (value?.assurance === "aal2" || value?.assurance === "aal3")
    && value?.phishingResistant === true
    && Array.isArray(value?.authMethods)
    && value.authMethods.includes("webauthn");
}
export function isTerminalRevocationJobState(value) {
  return value === "partial" || value === "succeeded" || value === "failed" || value === "cancelled";
}
