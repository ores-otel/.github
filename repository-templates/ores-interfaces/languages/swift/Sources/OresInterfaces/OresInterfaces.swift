import Foundation
public enum AuthMethod: String, Codable, Sendable { case jwt, oidc, webauthn, totp, kerberos, ssh, openpgp, platformBiometric = "platform_biometric", recovery }
public enum AssuranceLevel: String, Codable, Sendable { case aal0, aal1, aal2, aal3 }
public enum DirectoryAdminScope: String, Codable, Sendable {
  case dashboardRead = "directory.dashboard.read"
  case usersRead = "directory.users.read"
  case sessionsRead = "directory.sessions.read"
  case rolesRead = "directory.roles.read"
  case revocationsRead = "directory.revocations.read"
  case revocationsExecute = "directory.revocations.execute"
}
public enum DirectoryAdminRole: String, Codable, Sendable {
  case directoryAdmin = "directory_admin"
  case directorySecurityOperator = "directory_security_operator"
  case directoryAuditor = "directory_auditor"
}
public enum PrincipalSearchState: String, Codable, Sendable { case noMatch = "no_match", unique, ambiguous }
public enum InventoryStatus: String, Codable, Sendable { case complete, partial, unavailable }
public enum RevocationScope: String, Codable, Sendable {
  case interactiveSessions = "interactive_sessions"
  case refreshTokenFamilies = "refresh_token_families"
  case offlineGrants = "offline_grants"
  case downstreamSessions = "downstream_sessions"
  case impersonationSessions = "impersonation_sessions"
  case userApiCredentials = "user_api_credentials"
  case registeredDeviceSessions = "registered_device_sessions"
}
public enum RevocationJobState: String, Codable, Sendable {
  case queued, running, partial, succeeded, failed, cancelled
  public var terminal: Bool { self == .partial || self == .succeeded || self == .failed || self == .cancelled }
}
public enum RevocationTargetState: String, Codable, Sendable { case pending, running, retryScheduled = "retry_scheduled", succeeded, failed, skipped, unsupported }
public struct PrincipalRef: Codable, Sendable { public let tenantId: String; public let subject: String; public let kind: String; public let organization: String?; public let displayName: String? }
public struct PlatformBiometricProof: Codable, Sendable {
  public let verifiedByPlatformAuthenticator: Bool; public let userVerification: String; public let rawBiometricMaterialPresent: Bool
  public var safe: Bool { verifiedByPlatformAuthenticator && userVerification == "required" && !rawBiometricMaterialPresent }
}
public struct RevocationRedaction: Codable, Sendable {
  public let rawEmailsPresent: Bool; public let rawTokensPresent: Bool; public let rawSessionIdentifiersPresent: Bool; public let rawBiometricMaterialPresent: Bool
}
public struct ProviderIdentityRef: Codable, Sendable {
  public let providerId: String; public let providerTenantId: String; public let opaqueIdentityHandle: String
}
public struct PrincipalSearchRequest: Codable, Sendable {
  public let schema: String; public let requestId: String; public let requestedByPrincipalId: String; public let emailSearchKeyHash: String; public let purpose: String; public let requestedAt: String; public let redaction: RevocationRedaction
}
public struct PrincipalSearchCandidate: Codable, Sendable {
  public let principalId: String; public let identities: [ProviderIdentityRef]; public let organizationCount: UInt64; public let activeSessionCount: UInt64
}
public struct PrincipalSearchResult: Codable, Sendable {
  public let schema: String; public let lookupId: String; public let emailSearchKeyHash: String; public let state: PrincipalSearchState; public let candidates: [PrincipalSearchCandidate]; public let requiresExplicitPrincipalSelection: Bool; public let generatedAt: String; public let redaction: RevocationRedaction
}
public struct PrincipalSelectionRequest: Codable, Sendable {
  public let schema: String; public let requestId: String; public let lookupId: String; public let principalId: String; public let selectionConfirmed: Bool; public let requestedAt: String; public let redaction: RevocationRedaction
}
public struct PrincipalSelectionResult: Codable, Sendable {
  public let schema: String; public let selectionId: String; public let lookupId: String; public let principalId: String; public let selectedAt: String; public let expiresAt: String; public let redaction: RevocationRedaction
}
public struct GlobalRevocationPreviewRequest: Codable, Sendable {
  public let schema: String; public let requestId: String; public let selectionId: String; public let selectedScopes: [RevocationScope]; public let requestedAt: String; public let redaction: RevocationRedaction
}
public struct RevocationBlastRadius: Codable, Sendable {
  public let providerTenantCount: UInt64?; public let identityCount: UInt64?; public let organizationCount: UInt64?; public let projectCount: UInt64?; public let interactiveSessionCount: UInt64?; public let refreshTokenFamilyCount: UInt64?; public let offlineGrantCount: UInt64?; public let downstreamSessionCount: UInt64?; public let impersonationSessionCount: UInt64?; public let userApiCredentialCount: UInt64?; public let registeredDeviceSessionCount: UInt64?; public let inventoryStatus: InventoryStatus; public let unknownFields: [String]
}
public struct RevocationPreviewTarget: Codable, Sendable {
  public let targetIdHash: String; public let identity: ProviderIdentityRef; public let scope: RevocationScope; public let estimatedResourceCount: UInt64; public let supported: Bool; public let requiresProviderFanout: Bool; public let residualAccessTokenMaxSeconds: UInt64?; public let warningCodes: [String]
}
public struct GlobalRevocationPreview: Codable, Sendable {
  public let schema: String; public let previewId: String; public let principalId: String; public let generatedAt: String; public let expiresAt: String; public let selectedScopes: [RevocationScope]; public let blastRadius: RevocationBlastRadius; public let targets: [RevocationPreviewTarget]; public let ambiguityResolved: Bool; public let requiresStepUp: Bool; public let minimumAssurance: AssuranceLevel; public let phishingResistantStepUpRequired: Bool; public let redaction: RevocationRedaction
}
public struct RevocationStepUp: Codable, Sendable {
  public let actorPrincipalId: String; public let actorSessionIdHash: String; public let evidenceIdHash: String; public let assurance: AssuranceLevel; public let authMethods: [AuthMethod]; public let phishingResistant: Bool; public let verifiedAt: String; public let freshUntil: String
  public var sufficient: Bool { (assurance == .aal2 || assurance == .aal3) && phishingResistant && authMethods.contains(.webauthn) }
}
public struct RevocationRequestCorrelation: Codable, Sendable {
  public let requestId: String; public let traceId: String; public let reasonCode: String; public let ticketReferenceHash: String?
}
public struct GlobalRevocationRequest: Codable, Sendable {
  public let schema: String; public let previewId: String; public let commitAuthorizationId: String; public let idempotencyKey: String; public let selectedScopes: [RevocationScope]; public let requestedAt: String; public let correlation: RevocationRequestCorrelation; public let redaction: RevocationRedaction
}
public struct GlobalRevocationCommitAuthorization: Codable, Sendable {
  public let schema: String; public let commitAuthorizationId: String; public let previewId: String; public let principalId: String; public let selectedScopes: [RevocationScope]; public let previewCreatedByPrincipalIdHash: String; public let commitAuthorizedByPrincipalIdHash: String; public let commitAuthorizedBySessionIdHash: String; public let dualControlRequired: Bool; public let dualControlSatisfied: Bool; public let verifiedStepUp: RevocationStepUp; public let issuedAt: String; public let expiresAt: String; public let redaction: RevocationRedaction
}
public struct AdminTokenExchangeRedaction: Codable, Sendable {
  public let subjectTokenLogged: Bool; public let subjectTokenPersisted: Bool; public let accessTokenLogged: Bool; public let accessTokenPersisted: Bool; public let tokensReturnedInDiagnostics: Bool; public let rawEmailsPresent: Bool; public let rawBiometricMaterialPresent: Bool
}
public struct AdminRevocationTokenExchangeRequest: Codable, Sendable {
  public let schema: String; public let requestId: String; public let subjectToken: String; public let subjectTokenType: String; public let audience: String; public let requestedScope: String; public let requestedAt: String; public let redaction: AdminTokenExchangeRedaction
}
public struct AdminRevocationTokenExchangeResult: Codable, Sendable {
  public let schema: String; public let requestId: String; public let accessToken: String; public let issuedTokenType: String; public let tokenType: String; public let expiresInSeconds: UInt32; public let audience: String; public let authorizedParty: String; public let scope: String; public let issuedAt: String; public let expiresAt: String; public let redaction: AdminTokenExchangeRedaction
}
public struct RevocationTargetResult: Codable, Sendable {
  public let targetIdHash: String; public let identity: ProviderIdentityRef; public let scope: RevocationScope; public let state: RevocationTargetState; public let attemptCount: UInt32; public let retryable: Bool; public let lastAttemptAt: String?; public let nextAttemptAt: String?; public let retryAfterSeconds: UInt64?; public let completedAt: String?; public let resultCode: String?; public let providerRequestIdHash: String?; public let residualAccessTokenMaxSeconds: UInt64?
}
public struct RevocationFence: Codable, Sendable {
  public let appliedAt: String; public let notBefore: String; public let previousAuthEpoch: UInt64; public let authEpoch: UInt64; public let effective: Bool
}
public struct RevocationAuditCorrelation: Codable, Sendable {
  public let auditEventId: String; public let correlationId: String; public let requestId: String; public let traceId: String; public let actorPrincipalId: String; public let actorSessionIdHash: String; public let idempotencyKeyHash: String; public let reasonCode: String; public let rawEmailsPresent: Bool; public let rawTokensPresent: Bool; public let rawBiometricMaterialPresent: Bool
}
public struct GlobalRevocationOperation: Codable, Sendable {
  public let schema: String; public let operationId: String; public let principalId: String; public let previewId: String; public let state: RevocationJobState; public let selectedScopes: [RevocationScope]; public let createdAt: String; public let updatedAt: String; public let completedAt: String?; public let fence: RevocationFence; public let targets: [RevocationTargetResult]; public let audit: RevocationAuditCorrelation; public let redaction: RevocationRedaction
}
public struct DirectoryAdminGrant: Codable, Sendable {
  public let grantId: String; public let organizationId: String; public let projectIds: [String]?; public let scopes: [DirectoryAdminScope]; public let roles: [DirectoryAdminRole]; public let grantedAt: String; public let expiresAt: String?
  public var isDirectoryAdmin: Bool { roles.contains(.directoryAdmin) }
}
public struct DirectoryAdminGrantSet: Codable, Sendable {
  public let schema: String; public let principalId: String; public let audience: String; public let assurance: AssuranceLevel; public let directoryGrants: [DirectoryAdminGrant]; public let evaluatedAt: String; public let expiresAt: String; public let exactOrganizationMatchRequired: Bool; public let crossOrganizationFallbackAllowed: Bool; public let rawEmailsPresent: Bool
}
