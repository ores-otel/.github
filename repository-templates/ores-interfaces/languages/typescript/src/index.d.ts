export type AuthMethod = "jwt" | "oidc" | "webauthn" | "totp" | "kerberos" | "ssh" | "openpgp" | "platform_biometric" | "recovery";
export type AssuranceLevel = "aal0" | "aal1" | "aal2" | "aal3";
export type PrincipalKind = "human" | "service" | "workload" | "device" | "automation";
export interface PrincipalRef { tenantId: string; subject: string; kind: PrincipalKind; organization?: string; displayName?: string; }
export interface RequestContext { requestId: string; traceId: string; spanId?: string; tenantId?: string; clientId?: string; source?: string; }
export interface ErrorEnvelope { code: string; message: string; retryable: boolean; requestId: string; details?: Record<string, unknown>; }
export interface TokenClaims { iss: string; sub: string; aud: string[]; exp: number; iat: number; authTime?: number; jti: string; tenantId: string; sessionId: string; aal: AssuranceLevel; amr: AuthMethod[]; scopes: string[]; }
export interface PlatformBiometricProof { verifiedByPlatformAuthenticator: true; userVerification: "required"; modalityHint?: "face" | "fingerprint" | "unknown"; rawBiometricMaterialPresent: false; }
export type ResourceState = "active" | "suspended" | "archived";
export type UserState = "invited" | "active" | "suspended" | "deprovisioned";
export type MembershipState = "invited" | "active" | "suspended" | "removed";
export type SessionState = "active" | "revoked" | "expired";
export type FactorState = "pending" | "active" | "disabled" | "compromised";
export type RoleScopeKind = "organization" | "project" | "repository";
export interface Organization { organizationId: string; slug: string; displayName: string; state: ResourceState; createdAt: string; }
export interface Project { projectId: string; organizationId: string; slug: string; displayName: string; state: ResourceState; createdAt: string; }
/** Safe view: normalized email and lookup HMAC are deliberately absent. */
export interface User { userId: string; displayName: string; emailRedacted: string; state: UserState; createdAt: string; lastAuthenticatedAt?: string; }
export interface Membership { membershipId: string; organizationId: string; userId: string; state: MembershipState; joinedAt?: string; }
export interface Role { roleId: string; organizationId: string; key: string; displayName: string; permissions: string[]; }
export interface RoleBinding { roleBindingId: string; organizationId: string; membershipId: string; roleId: string; scopeKind: RoleScopeKind; scopeId: string; grantedAt: string; expiresAt?: string; }
/** `sessionIdHash` is a non-reversible display/audit identifier, never a bearer credential. */
export interface Session { sessionIdHash: string; userId: string; organizationId: string; projectId?: string; clientId: string; state: SessionState; assurance: AssuranceLevel; authMethods: AuthMethod[]; createdAt: string; expiresAt: string; revokedAt?: string; }
/** Credential metadata only; private keys and biometric material have no representation. */
export interface Factor { factorId: string; userId: string; method: AuthMethod; state: FactorState; externalCredentialRefHash?: string; publicKeyFingerprint?: string; rawBiometricMaterialPresent: false; privateKeyMaterialPresent: false; createdAt: string; lastUsedAt?: string; }
export interface AuditEvent { auditEventId: string; organizationId?: string; projectId?: string; actorSubject: string; action: string; targetKind: string; targetIdHash: string; outcome: "allowed" | "denied" | "succeeded" | "failed"; reasonCode?: string; requestId: string; traceId: string; occurredAt: string; sensitiveMaterialPresent: false; }
export type RevocationScope = {mode: "all_authorized_organizations"} | {mode: "selected_organizations"; organizationIds: string[]};
export type RevocationReason = "admin_action" | "compromised" | "incident_response" | "offboarding" | "user_request";
export type RevocationStatus = "completed" | "partial" | "denied" | "no_match";
/** `normalizedEmail` is write-only and must be discarded after deriving a keyed HMAC. */
export interface RevokeSessionsByEmailRequest { requestId: string; idempotencyKey: string; normalizedEmail: string; scope: RevocationScope; reason: RevocationReason; dryRun: boolean; }
export interface OrganizationRevocationResult { organizationId: string; outcome: "revoked" | "no_active_sessions" | "failed"; matchedUsers: number; sessionsRevoked: number; sessionsAlreadyInactive: number; errorCode?: string; authorizationVerified: true; }
/** Sanitized result; an email field is intentionally impossible. */
export interface RevokeSessionsByEmailResult { requestId: string; idempotencyKey: string; operationId: string; status: RevocationStatus; replayed: boolean; dryRun: boolean; authorizedOrganizationCount: number; unprocessedOrganizationCount: number; matchedUsers: number; sessionsRevoked: number; sessionsAlreadyInactive: number; organizationResults: OrganizationRevocationResult[]; authorizationPolicy: "per_organization_sessions.revoke"; onlyAuthorizedOrganizationsProcessed: true; completedAt: string; }
export declare const AuthMethod: Readonly<Record<string, AuthMethod>>;
export declare const AssuranceLevel: Readonly<Record<string, AssuranceLevel>>;
export declare function isSafePlatformBiometricProof(value: unknown): value is PlatformBiometricProof;
