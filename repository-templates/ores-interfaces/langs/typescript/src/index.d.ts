export type AuthMethod = "jwt" | "oidc" | "webauthn" | "totp" | "kerberos" | "ssh" | "openpgp" | "platform_biometric" | "recovery";
export type AssuranceLevel = "aal0" | "aal1" | "aal2" | "aal3";
export type DirectoryAdminScope = "directory.dashboard.read" | "directory.users.read" | "directory.sessions.read" | "directory.roles.read" | "directory.revocations.read" | "directory.revocations.execute";
export type DirectoryAdminRole = "directory_admin" | "directory_security_operator" | "directory_auditor";
export type PrincipalSearchState = "no_match" | "unique" | "ambiguous";
export type InventoryStatus = "complete" | "partial" | "unavailable";
export type RevocationScope = "interactive_sessions" | "refresh_token_families" | "offline_grants" | "downstream_sessions" | "impersonation_sessions" | "user_api_credentials" | "registered_device_sessions";
export type RevocationJobState = "queued" | "running" | "partial" | "succeeded" | "failed" | "cancelled";
export type RevocationTargetState = "pending" | "running" | "retry_scheduled" | "succeeded" | "failed" | "skipped" | "unsupported";
export type PrincipalKind = "human" | "service" | "workload" | "device" | "automation";
export interface PrincipalRef { tenantId: string; subject: string; kind: PrincipalKind; organization?: string; displayName?: string; }
export interface RequestContext { requestId: string; traceId: string; spanId?: string; tenantId?: string; clientId?: string; source?: string; }
export interface ErrorEnvelope { code: string; message: string; retryable: boolean; requestId: string; details?: Record<string, unknown>; }
export interface TokenClaims { iss: string; sub: string; aud: string[]; exp: number; iat: number; authTime?: number; jti: string; tenantId: string; sessionId: string; aal: AssuranceLevel; amr: AuthMethod[]; scopes: string[]; }
export interface PlatformBiometricProof { verifiedByPlatformAuthenticator: true; userVerification: "required"; modalityHint?: "face" | "fingerprint" | "unknown"; rawBiometricMaterialPresent: false; }
export interface RevocationRedaction { rawEmailsPresent: false; rawTokensPresent: false; rawSessionIdentifiersPresent: false; rawBiometricMaterialPresent: false; }
export interface ProviderIdentityRef { providerId: string; providerTenantId: string; opaqueIdentityHandle: string; }
export interface PrincipalSearchRequest { schema: "ores.shared-auth-admin-principal-search-request/v1"; requestId: string; requestedByPrincipalId: string; emailSearchKeyHash: string; purpose: "operator_email_search"; requestedAt: string; redaction: RevocationRedaction; }
export interface PrincipalSearchCandidate { principalId: string; identities: ProviderIdentityRef[]; organizationCount: number; activeSessionCount: number; }
export interface PrincipalSearchResult { schema: "ores.shared-auth-admin-principal-search-result/v1"; lookupId: string; emailSearchKeyHash: string; state: PrincipalSearchState; candidates: PrincipalSearchCandidate[]; requiresExplicitPrincipalSelection: boolean; generatedAt: string; redaction: RevocationRedaction; }
export interface PrincipalSelectionRequest { schema: "ores.shared-auth-admin-principal-selection-request/v1"; requestId: string; lookupId: string; principalId: string; selectionConfirmed: true; requestedAt: string; redaction: RevocationRedaction; }
export interface PrincipalSelectionResult { schema: "ores.shared-auth-admin-principal-selection-result/v1"; selectionId: string; lookupId: string; principalId: string; selectedAt: string; expiresAt: string; redaction: RevocationRedaction; }
export interface GlobalRevocationPreviewRequest { schema: "ores.shared-auth-admin-global-revocation-preview-request/v1"; requestId: string; selectionId: string; selectedScopes: RevocationScope[]; requestedAt: string; redaction: RevocationRedaction; }
export interface RevocationBlastRadius { providerTenantCount: number | null; identityCount: number | null; organizationCount: number | null; projectCount: number | null; interactiveSessionCount: number | null; refreshTokenFamilyCount: number | null; offlineGrantCount: number | null; downstreamSessionCount: number | null; impersonationSessionCount: number | null; userApiCredentialCount: number | null; registeredDeviceSessionCount: number | null; inventoryStatus: InventoryStatus; unknownFields: string[]; }
export interface RevocationPreviewTarget { targetIdHash: string; identity: ProviderIdentityRef; scope: RevocationScope; estimatedResourceCount: number; supported: boolean; requiresProviderFanout: boolean; residualAccessTokenMaxSeconds: number | null; warningCodes: string[]; }
export interface GlobalRevocationPreview { schema: "ores.shared-auth-admin-global-revocation-preview/v1"; previewId: string; principalId: string; generatedAt: string; expiresAt: string; selectedScopes: RevocationScope[]; blastRadius: RevocationBlastRadius; targets: RevocationPreviewTarget[]; ambiguityResolved: true; requiresStepUp: true; minimumAssurance: "aal2"; phishingResistantStepUpRequired: true; redaction: RevocationRedaction; }
export interface RevocationStepUp { actorPrincipalId: string; actorSessionIdHash: string; evidenceIdHash: string; assurance: "aal2" | "aal3"; authMethods: AuthMethod[]; phishingResistant: true; verifiedAt: string; freshUntil: string; }
export interface RevocationRequestCorrelation { requestId: string; traceId: string; reasonCode: string; ticketReferenceHash?: string; }
export interface GlobalRevocationRequest { schema: "ores.shared-auth-admin-global-revocation-request/v1"; previewId: string; commitAuthorizationId: string; idempotencyKey: string; selectedScopes: RevocationScope[]; requestedAt: string; correlation: RevocationRequestCorrelation; redaction: RevocationRedaction; }
export interface GlobalRevocationCommitAuthorization { schema: "ores.shared-auth-admin-global-revocation-commit-authorization/v1"; commitAuthorizationId: string; previewId: string; principalId: string; selectedScopes: RevocationScope[]; previewCreatedByPrincipalIdHash: string; commitAuthorizedByPrincipalIdHash: string; commitAuthorizedBySessionIdHash: string; dualControlRequired: boolean; dualControlSatisfied: true; verifiedStepUp: RevocationStepUp; issuedAt: string; expiresAt: string; redaction: RevocationRedaction; }
export interface AdminTokenExchangeRedaction { subjectTokenLogged: false; subjectTokenPersisted: false; accessTokenLogged: false; accessTokenPersisted: false; tokensReturnedInDiagnostics: false; rawEmailsPresent: false; rawBiometricMaterialPresent: false; }
export interface AdminRevocationTokenExchangeRequest { schema: "ores.shared-auth-admin-revocation-token-exchange-request/v1"; requestId: string; subjectToken: string; subjectTokenType: "urn:ietf:params:oauth:token-type:access_token"; audience: "shared-auth-web-server"; requestedScope: "shared-auth:sessions:revoke:global"; requestedAt: string; redaction: AdminTokenExchangeRedaction; }
export interface AdminRevocationTokenExchangeResult { schema: "ores.shared-auth-admin-revocation-token-exchange-result/v1"; requestId: string; accessToken: string; issuedTokenType: "urn:ietf:params:oauth:token-type:access_token"; tokenType: "Bearer"; expiresInSeconds: number; audience: "shared-auth-web-server"; authorizedParty: "shared-auth-web-server"; scope: "shared-auth:sessions:revoke:global"; issuedAt: string; expiresAt: string; redaction: AdminTokenExchangeRedaction; }
export interface RevocationTargetResult { targetIdHash: string; identity: ProviderIdentityRef; scope: RevocationScope; state: RevocationTargetState; attemptCount: number; retryable: boolean; lastAttemptAt?: string; nextAttemptAt?: string; retryAfterSeconds?: number; completedAt?: string; resultCode?: string; providerRequestIdHash?: string; residualAccessTokenMaxSeconds: number | null; }
export interface RevocationFence { appliedAt: string; notBefore: string; previousAuthEpoch: number; authEpoch: number; effective: true; }
export interface RevocationAuditCorrelation { auditEventId: string; correlationId: string; requestId: string; traceId: string; actorPrincipalId: string; actorSessionIdHash: string; idempotencyKeyHash: string; reasonCode: string; rawEmailsPresent: false; rawTokensPresent: false; rawBiometricMaterialPresent: false; }
export interface GlobalRevocationOperation { schema: "ores.shared-auth-admin-global-revocation-operation/v1"; operationId: string; principalId: string; previewId: string; state: RevocationJobState; selectedScopes: RevocationScope[]; createdAt: string; updatedAt: string; completedAt?: string; fence: RevocationFence; targets: RevocationTargetResult[]; audit: RevocationAuditCorrelation; redaction: RevocationRedaction; }
export interface DirectoryAdminGrant { grantId: string; organizationId: string; projectIds?: string[]; scopes: DirectoryAdminScope[]; roles: DirectoryAdminRole[]; grantedAt: string; expiresAt?: string; }
export interface DirectoryAdminGrantSet { schema: "ores.shared-auth-admin-directory-grant-set/v1"; principalId: string; audience: string; assurance: "aal2" | "aal3"; directoryGrants: DirectoryAdminGrant[]; evaluatedAt: string; expiresAt: string; exactOrganizationMatchRequired: true; crossOrganizationFallbackAllowed: false; rawEmailsPresent: false; }

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
export type EmailRevocationScope = {mode: "all_authorized_organizations"} | {mode: "selected_organizations"; organizationIds: string[]};
export type EmailRevocationReason = "admin_action" | "compromised" | "incident_response" | "offboarding" | "user_request";
export type EmailRevocationStatus = "completed" | "partial" | "denied" | "no_match";
/** `normalizedEmail` is write-only and must be discarded after deriving a keyed HMAC. */
export interface RevokeSessionsByEmailRequest { requestId: string; idempotencyKey: string; normalizedEmail: string; scope: EmailRevocationScope; reason: EmailRevocationReason; dryRun: boolean; }
export interface OrganizationRevocationResult { organizationId: string; outcome: "revoked" | "no_active_sessions" | "failed"; matchedUsers: number; sessionsRevoked: number; sessionsAlreadyInactive: number; errorCode?: string; authorizationVerified: true; }
/** Sanitized result; an email field is intentionally impossible. */
export interface RevokeSessionsByEmailResult { requestId: string; idempotencyKey: string; operationId: string; status: EmailRevocationStatus; replayed: boolean; dryRun: boolean; authorizedOrganizationCount: number; unprocessedOrganizationCount: number; matchedUsers: number; sessionsRevoked: number; sessionsAlreadyInactive: number; organizationResults: OrganizationRevocationResult[]; authorizationPolicy: "per_organization_sessions.revoke"; onlyAuthorizedOrganizationsProcessed: true; completedAt: string; }

export declare const AuthMethod: Readonly<Record<string, AuthMethod>>;
export declare const AssuranceLevel: Readonly<Record<string, AssuranceLevel>>;
export declare const DirectoryAdminScope: Readonly<Record<string, DirectoryAdminScope>>;
export declare const DirectoryAdminRole: Readonly<Record<string, DirectoryAdminRole>>;
export declare const PrincipalSearchState: Readonly<Record<string, PrincipalSearchState>>;
export declare const InventoryStatus: Readonly<Record<string, InventoryStatus>>;
export declare const RevocationScope: Readonly<Record<string, RevocationScope>>;
export declare const RevocationJobState: Readonly<Record<string, RevocationJobState>>;
export declare const RevocationTargetState: Readonly<Record<string, RevocationTargetState>>;
export declare function isSafePlatformBiometricProof(value: unknown): value is PlatformBiometricProof;
export declare function isSufficientRevocationStepUp(value: unknown): value is RevocationStepUp;
export declare function isTerminalRevocationJobState(value: RevocationJobState): boolean;
