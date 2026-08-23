enum AuthMethod {
  jwt,
  oidc,
  webauthn,
  totp,
  kerberos,
  ssh,
  openpgp,
  platformBiometric,
  recovery,
}

enum AssuranceLevel { aal0, aal1, aal2, aal3 }

enum DirectoryAdminScope {
  dashboardRead('directory.dashboard.read'),
  usersRead('directory.users.read'),
  sessionsRead('directory.sessions.read'),
  rolesRead('directory.roles.read'),
  revocationsRead('directory.revocations.read'),
  revocationsExecute('directory.revocations.execute');

  const DirectoryAdminScope(this.wireValue);
  final String wireValue;
}

enum DirectoryAdminRole {
  directoryAdmin('directory_admin'),
  directorySecurityOperator('directory_security_operator'),
  directoryAuditor('directory_auditor');

  const DirectoryAdminRole(this.wireValue);
  final String wireValue;
}

enum PrincipalSearchState {
  noMatch('no_match'),
  unique('unique'),
  ambiguous('ambiguous');

  const PrincipalSearchState(this.wireValue);
  final String wireValue;
}

enum InventoryStatus {
  complete('complete'),
  partial('partial'),
  unavailable('unavailable');

  const InventoryStatus(this.wireValue);
  final String wireValue;
}

enum RevocationScope {
  interactiveSessions('interactive_sessions'),
  refreshTokenFamilies('refresh_token_families'),
  offlineGrants('offline_grants'),
  downstreamSessions('downstream_sessions'),
  impersonationSessions('impersonation_sessions'),
  userApiCredentials('user_api_credentials'),
  registeredDeviceSessions('registered_device_sessions');

  const RevocationScope(this.wireValue);
  final String wireValue;
}

enum RevocationJobState {
  queued('queued', false),
  running('running', false),
  partial('partial', true),
  succeeded('succeeded', true),
  failed('failed', true),
  cancelled('cancelled', true);

  const RevocationJobState(this.wireValue, this.terminal);
  final String wireValue;
  final bool terminal;
}

enum RevocationTargetState {
  pending('pending'),
  running('running'),
  retryScheduled('retry_scheduled'),
  succeeded('succeeded'),
  failed('failed'),
  skipped('skipped'),
  unsupported('unsupported');

  const RevocationTargetState(this.wireValue);
  final String wireValue;
}

final class PrincipalRef {
  const PrincipalRef({
    required this.tenantId,
    required this.subject,
    required this.kind,
    this.organization,
    this.displayName,
  });
  final String tenantId;
  final String subject;
  final String kind;
  final String? organization;
  final String? displayName;
}

final class PlatformBiometricProof {
  const PlatformBiometricProof({
    required this.verifiedByPlatformAuthenticator,
    required this.userVerification,
    this.rawBiometricMaterialPresent = false,
  });
  final bool verifiedByPlatformAuthenticator;
  final String userVerification;
  final bool rawBiometricMaterialPresent;
  bool get safe =>
      verifiedByPlatformAuthenticator &&
      userVerification == 'required' &&
      !rawBiometricMaterialPresent;
}

final class RevocationRedaction {
  const RevocationRedaction({
    required this.rawEmailsPresent,
    required this.rawTokensPresent,
    required this.rawSessionIdentifiersPresent,
    required this.rawBiometricMaterialPresent,
  });
  final bool rawEmailsPresent;
  final bool rawTokensPresent;
  final bool rawSessionIdentifiersPresent;
  final bool rawBiometricMaterialPresent;
}

final class ProviderIdentityRef {
  const ProviderIdentityRef({
    required this.providerId,
    required this.providerTenantId,
    required this.opaqueIdentityHandle,
  });
  final String providerId;
  final String providerTenantId;
  final String opaqueIdentityHandle;
}

final class PrincipalSearchRequest {
  const PrincipalSearchRequest({
    required this.schema,
    required this.requestId,
    required this.requestedByPrincipalId,
    required this.emailSearchKeyHash,
    required this.purpose,
    required this.requestedAt,
    required this.redaction,
  });
  final String schema;
  final String requestId;
  final String requestedByPrincipalId;
  final String emailSearchKeyHash;
  final String purpose;
  final String requestedAt;
  final RevocationRedaction redaction;
}

final class PrincipalSearchCandidate {
  const PrincipalSearchCandidate({
    required this.principalId,
    required this.identities,
    required this.organizationCount,
    required this.activeSessionCount,
  });
  final String principalId;
  final List<ProviderIdentityRef> identities;
  final int organizationCount;
  final int activeSessionCount;
}

final class PrincipalSearchResult {
  const PrincipalSearchResult({
    required this.schema,
    required this.lookupId,
    required this.emailSearchKeyHash,
    required this.state,
    required this.candidates,
    required this.requiresExplicitPrincipalSelection,
    required this.generatedAt,
    required this.redaction,
  });
  final String schema;
  final String lookupId;
  final String emailSearchKeyHash;
  final PrincipalSearchState state;
  final List<PrincipalSearchCandidate> candidates;
  final bool requiresExplicitPrincipalSelection;
  final String generatedAt;
  final RevocationRedaction redaction;
}

final class PrincipalSelectionRequest {
  const PrincipalSelectionRequest({
    required this.schema,
    required this.requestId,
    required this.lookupId,
    required this.principalId,
    required this.selectionConfirmed,
    required this.requestedAt,
    required this.redaction,
  });
  final String schema;
  final String requestId;
  final String lookupId;
  final String principalId;
  final bool selectionConfirmed;
  final String requestedAt;
  final RevocationRedaction redaction;
}

final class PrincipalSelectionResult {
  const PrincipalSelectionResult({
    required this.schema,
    required this.selectionId,
    required this.lookupId,
    required this.principalId,
    required this.selectedAt,
    required this.expiresAt,
    required this.redaction,
  });
  final String schema;
  final String selectionId;
  final String lookupId;
  final String principalId;
  final String selectedAt;
  final String expiresAt;
  final RevocationRedaction redaction;
}

final class GlobalRevocationPreviewRequest {
  const GlobalRevocationPreviewRequest({
    required this.schema,
    required this.requestId,
    required this.selectionId,
    required this.selectedScopes,
    required this.requestedAt,
    required this.redaction,
  });
  final String schema;
  final String requestId;
  final String selectionId;
  final List<RevocationScope> selectedScopes;
  final String requestedAt;
  final RevocationRedaction redaction;
}

final class RevocationBlastRadius {
  const RevocationBlastRadius({
    required this.providerTenantCount,
    required this.identityCount,
    required this.organizationCount,
    required this.projectCount,
    required this.interactiveSessionCount,
    required this.refreshTokenFamilyCount,
    required this.offlineGrantCount,
    required this.downstreamSessionCount,
    required this.impersonationSessionCount,
    required this.userApiCredentialCount,
    required this.registeredDeviceSessionCount,
    required this.inventoryStatus,
    required this.unknownFields,
  });
  final int? providerTenantCount;
  final int? identityCount;
  final int? organizationCount;
  final int? projectCount;
  final int? interactiveSessionCount;
  final int? refreshTokenFamilyCount;
  final int? offlineGrantCount;
  final int? downstreamSessionCount;
  final int? impersonationSessionCount;
  final int? userApiCredentialCount;
  final int? registeredDeviceSessionCount;
  final InventoryStatus inventoryStatus;
  final List<String> unknownFields;
}

final class RevocationPreviewTarget {
  const RevocationPreviewTarget({
    required this.targetIdHash,
    required this.identity,
    required this.scope,
    required this.estimatedResourceCount,
    required this.supported,
    required this.requiresProviderFanout,
    required this.residualAccessTokenMaxSeconds,
    required this.warningCodes,
  });
  final String targetIdHash;
  final ProviderIdentityRef identity;
  final RevocationScope scope;
  final int estimatedResourceCount;
  final bool supported;
  final bool requiresProviderFanout;
  final int? residualAccessTokenMaxSeconds;
  final List<String> warningCodes;
}

final class GlobalRevocationPreview {
  const GlobalRevocationPreview({
    required this.schema,
    required this.previewId,
    required this.principalId,
    required this.generatedAt,
    required this.expiresAt,
    required this.selectedScopes,
    required this.blastRadius,
    required this.targets,
    required this.ambiguityResolved,
    required this.requiresStepUp,
    required this.minimumAssurance,
    required this.phishingResistantStepUpRequired,
    required this.redaction,
  });
  final String schema;
  final String previewId;
  final String principalId;
  final String generatedAt;
  final String expiresAt;
  final List<RevocationScope> selectedScopes;
  final RevocationBlastRadius blastRadius;
  final List<RevocationPreviewTarget> targets;
  final bool ambiguityResolved;
  final bool requiresStepUp;
  final AssuranceLevel minimumAssurance;
  final bool phishingResistantStepUpRequired;
  final RevocationRedaction redaction;
}

final class RevocationStepUp {
  const RevocationStepUp({
    required this.actorPrincipalId,
    required this.actorSessionIdHash,
    required this.evidenceIdHash,
    required this.assurance,
    required this.authMethods,
    required this.phishingResistant,
    required this.verifiedAt,
    required this.freshUntil,
  });
  final String actorPrincipalId;
  final String actorSessionIdHash;
  final String evidenceIdHash;
  final AssuranceLevel assurance;
  final List<AuthMethod> authMethods;
  final bool phishingResistant;
  final String verifiedAt;
  final String freshUntil;
  bool get sufficient =>
      (assurance == AssuranceLevel.aal2 || assurance == AssuranceLevel.aal3) &&
      phishingResistant &&
      authMethods.contains(AuthMethod.webauthn);
}

final class RevocationRequestCorrelation {
  const RevocationRequestCorrelation({
    required this.requestId,
    required this.traceId,
    required this.reasonCode,
    this.ticketReferenceHash,
  });
  final String requestId;
  final String traceId;
  final String reasonCode;
  final String? ticketReferenceHash;
}

final class GlobalRevocationRequest {
  const GlobalRevocationRequest({
    required this.schema,
    required this.previewId,
    required this.commitAuthorizationId,
    required this.idempotencyKey,
    required this.selectedScopes,
    required this.requestedAt,
    required this.correlation,
    required this.redaction,
  });
  final String schema;
  final String previewId;
  final String commitAuthorizationId;
  final String idempotencyKey;
  final List<RevocationScope> selectedScopes;
  final String requestedAt;
  final RevocationRequestCorrelation correlation;
  final RevocationRedaction redaction;
}

final class GlobalRevocationCommitAuthorization {
  const GlobalRevocationCommitAuthorization({
    required this.schema,
    required this.commitAuthorizationId,
    required this.previewId,
    required this.principalId,
    required this.selectedScopes,
    required this.previewCreatedByPrincipalIdHash,
    required this.commitAuthorizedByPrincipalIdHash,
    required this.commitAuthorizedBySessionIdHash,
    required this.dualControlRequired,
    required this.dualControlSatisfied,
    required this.verifiedStepUp,
    required this.issuedAt,
    required this.expiresAt,
    required this.redaction,
  });
  final String schema;
  final String commitAuthorizationId;
  final String previewId;
  final String principalId;
  final List<RevocationScope> selectedScopes;
  final String previewCreatedByPrincipalIdHash;
  final String commitAuthorizedByPrincipalIdHash;
  final String commitAuthorizedBySessionIdHash;
  final bool dualControlRequired;
  final bool dualControlSatisfied;
  final RevocationStepUp verifiedStepUp;
  final String issuedAt;
  final String expiresAt;
  final RevocationRedaction redaction;
}

final class AdminTokenExchangeRedaction {
  const AdminTokenExchangeRedaction({
    required this.subjectTokenLogged,
    required this.subjectTokenPersisted,
    required this.accessTokenLogged,
    required this.accessTokenPersisted,
    required this.tokensReturnedInDiagnostics,
    required this.rawEmailsPresent,
    required this.rawBiometricMaterialPresent,
  });
  final bool subjectTokenLogged;
  final bool subjectTokenPersisted;
  final bool accessTokenLogged;
  final bool accessTokenPersisted;
  final bool tokensReturnedInDiagnostics;
  final bool rawEmailsPresent;
  final bool rawBiometricMaterialPresent;
}

final class AdminRevocationTokenExchangeRequest {
  const AdminRevocationTokenExchangeRequest({
    required this.schema,
    required this.requestId,
    required this.subjectToken,
    required this.subjectTokenType,
    required this.audience,
    required this.requestedScope,
    required this.requestedAt,
    required this.redaction,
  });
  final String schema;
  final String requestId;
  final String subjectToken;
  final String subjectTokenType;
  final String audience;
  final String requestedScope;
  final String requestedAt;
  final AdminTokenExchangeRedaction redaction;
}

final class AdminRevocationTokenExchangeResult {
  const AdminRevocationTokenExchangeResult({
    required this.schema,
    required this.requestId,
    required this.accessToken,
    required this.issuedTokenType,
    required this.tokenType,
    required this.expiresInSeconds,
    required this.audience,
    required this.authorizedParty,
    required this.scope,
    required this.issuedAt,
    required this.expiresAt,
    required this.redaction,
  });
  final String schema;
  final String requestId;
  final String accessToken;
  final String issuedTokenType;
  final String tokenType;
  final int expiresInSeconds;
  final String audience;
  final String authorizedParty;
  final String scope;
  final String issuedAt;
  final String expiresAt;
  final AdminTokenExchangeRedaction redaction;
}

final class RevocationTargetResult {
  const RevocationTargetResult({
    required this.targetIdHash,
    required this.identity,
    required this.scope,
    required this.state,
    required this.attemptCount,
    required this.retryable,
    this.lastAttemptAt,
    this.nextAttemptAt,
    this.retryAfterSeconds,
    this.completedAt,
    this.resultCode,
    this.providerRequestIdHash,
    required this.residualAccessTokenMaxSeconds,
  });
  final String targetIdHash;
  final ProviderIdentityRef identity;
  final RevocationScope scope;
  final RevocationTargetState state;
  final int attemptCount;
  final bool retryable;
  final String? lastAttemptAt;
  final String? nextAttemptAt;
  final int? retryAfterSeconds;
  final String? completedAt;
  final String? resultCode;
  final String? providerRequestIdHash;
  final int? residualAccessTokenMaxSeconds;
}

final class RevocationFence {
  const RevocationFence({
    required this.appliedAt,
    required this.notBefore,
    required this.previousAuthEpoch,
    required this.authEpoch,
    required this.effective,
  });
  final String appliedAt;
  final String notBefore;
  final int previousAuthEpoch;
  final int authEpoch;
  final bool effective;
}

final class RevocationAuditCorrelation {
  const RevocationAuditCorrelation({
    required this.auditEventId,
    required this.correlationId,
    required this.requestId,
    required this.traceId,
    required this.actorPrincipalId,
    required this.actorSessionIdHash,
    required this.idempotencyKeyHash,
    required this.reasonCode,
    required this.rawEmailsPresent,
    required this.rawTokensPresent,
    required this.rawBiometricMaterialPresent,
  });
  final String auditEventId;
  final String correlationId;
  final String requestId;
  final String traceId;
  final String actorPrincipalId;
  final String actorSessionIdHash;
  final String idempotencyKeyHash;
  final String reasonCode;
  final bool rawEmailsPresent;
  final bool rawTokensPresent;
  final bool rawBiometricMaterialPresent;
}

final class GlobalRevocationOperation {
  const GlobalRevocationOperation({
    required this.schema,
    required this.operationId,
    required this.principalId,
    required this.previewId,
    required this.state,
    required this.selectedScopes,
    required this.createdAt,
    required this.updatedAt,
    this.completedAt,
    required this.fence,
    required this.targets,
    required this.audit,
    required this.redaction,
  });
  final String schema;
  final String operationId;
  final String principalId;
  final String previewId;
  final RevocationJobState state;
  final List<RevocationScope> selectedScopes;
  final String createdAt;
  final String updatedAt;
  final String? completedAt;
  final RevocationFence fence;
  final List<RevocationTargetResult> targets;
  final RevocationAuditCorrelation audit;
  final RevocationRedaction redaction;
}

final class DirectoryAdminGrant {
  const DirectoryAdminGrant({
    required this.grantId,
    required this.organizationId,
    this.projectIds,
    required this.scopes,
    required this.roles,
    required this.grantedAt,
    this.expiresAt,
  });
  final String grantId;
  final String organizationId;
  final List<String>? projectIds;
  final List<DirectoryAdminScope> scopes;
  final List<DirectoryAdminRole> roles;
  final String grantedAt;
  final String? expiresAt;
  bool get isDirectoryAdmin =>
      roles.contains(DirectoryAdminRole.directoryAdmin);
}

final class DirectoryAdminGrantSet {
  const DirectoryAdminGrantSet({
    required this.schema,
    required this.principalId,
    required this.audience,
    required this.assurance,
    required this.directoryGrants,
    required this.evaluatedAt,
    required this.expiresAt,
    required this.exactOrganizationMatchRequired,
    required this.crossOrganizationFallbackAllowed,
    required this.rawEmailsPresent,
  });
  final String schema;
  final String principalId;
  final String audience;
  final AssuranceLevel assurance;
  final List<DirectoryAdminGrant> directoryGrants;
  final String evaluatedAt;
  final String expiresAt;
  final bool exactOrganizationMatchRequired;
  final bool crossOrganizationFallbackAllowed;
  final bool rawEmailsPresent;
}

// Email revocation is a distinct organization-authorized domain from the global control plane.
enum ResourceState { active, suspended, archived }

enum UserState { invited, active, suspended, deprovisioned }

enum MembershipState { invited, active, suspended, removed }

enum SessionState { active, revoked, expired }

enum FactorState { pending, active, disabled, compromised }

enum RoleScopeKind { organization, project, repository }

final class Organization {
  const Organization(
      {required this.organizationId,
      required this.slug,
      required this.displayName,
      required this.state,
      required this.createdAt});
  final String organizationId;
  final String slug;
  final String displayName;
  final ResourceState state;
  final String createdAt;
}

final class Project {
  const Project(
      {required this.projectId,
      required this.organizationId,
      required this.slug,
      required this.displayName,
      required this.state,
      required this.createdAt});
  final String projectId;
  final String organizationId;
  final String slug;
  final String displayName;
  final ResourceState state;
  final String createdAt;
}

/// Safe projection: normalized email and its lookup HMAC are deliberately absent.
final class User {
  const User(
      {required this.userId,
      required this.displayName,
      required this.emailRedacted,
      required this.state,
      required this.createdAt,
      this.lastAuthenticatedAt});
  final String userId;
  final String displayName;
  final String emailRedacted;
  final UserState state;
  final String createdAt;
  final String? lastAuthenticatedAt;
}

final class Membership {
  const Membership(
      {required this.membershipId,
      required this.organizationId,
      required this.userId,
      required this.state,
      this.joinedAt});
  final String membershipId;
  final String organizationId;
  final String userId;
  final MembershipState state;
  final String? joinedAt;
}

final class Role {
  const Role(
      {required this.roleId,
      required this.organizationId,
      required this.key,
      required this.displayName,
      required this.permissions});
  final String roleId;
  final String organizationId;
  final String key;
  final String displayName;
  final List<String> permissions;
}

final class RoleBinding {
  const RoleBinding(
      {required this.roleBindingId,
      required this.organizationId,
      required this.membershipId,
      required this.roleId,
      required this.scopeKind,
      required this.scopeId,
      required this.grantedAt,
      this.expiresAt});
  final String roleBindingId;
  final String organizationId;
  final String membershipId;
  final String roleId;
  final RoleScopeKind scopeKind;
  final String scopeId;
  final String grantedAt;
  final String? expiresAt;
}

/// `sessionIdHash` is a non-reversible display/audit value, never a bearer credential.
final class Session {
  const Session(
      {required this.sessionIdHash,
      required this.userId,
      required this.organizationId,
      this.projectId,
      required this.clientId,
      required this.state,
      required this.assurance,
      required this.authMethods,
      required this.createdAt,
      required this.expiresAt,
      this.revokedAt});
  final String sessionIdHash;
  final String userId;
  final String organizationId;
  final String? projectId;
  final String clientId;
  final SessionState state;
  final AssuranceLevel assurance;
  final List<AuthMethod> authMethods;
  final String createdAt;
  final String expiresAt;
  final String? revokedAt;
}

/// Credential metadata only; private keys and biometric material have no representation.
final class Factor {
  const Factor(
      {required this.factorId,
      required this.userId,
      required this.method,
      required this.state,
      this.externalCredentialRefHash,
      this.publicKeyFingerprint,
      this.rawBiometricMaterialPresent = false,
      this.privateKeyMaterialPresent = false,
      required this.createdAt,
      this.lastUsedAt});
  final String factorId;
  final String userId;
  final AuthMethod method;
  final FactorState state;
  final String? externalCredentialRefHash;
  final String? publicKeyFingerprint;
  final bool rawBiometricMaterialPresent;
  final bool privateKeyMaterialPresent;
  final String createdAt;
  final String? lastUsedAt;
  bool get safe => !rawBiometricMaterialPresent && !privateKeyMaterialPresent;
}

final class AuditEvent {
  const AuditEvent(
      {required this.auditEventId,
      this.organizationId,
      this.projectId,
      required this.actorSubject,
      required this.action,
      required this.targetKind,
      required this.targetIdHash,
      required this.outcome,
      this.reasonCode,
      required this.requestId,
      required this.traceId,
      required this.occurredAt,
      this.sensitiveMaterialPresent = false});
  final String auditEventId;
  final String? organizationId;
  final String? projectId;
  final String actorSubject;
  final String action;
  final String targetKind;
  final String targetIdHash;
  final String outcome;
  final String? reasonCode;
  final String requestId;
  final String traceId;
  final String occurredAt;
  final bool sensitiveMaterialPresent;
  bool get safe => !sensitiveMaterialPresent;
}

enum EmailRevocationScopeMode {
  allAuthorizedOrganizations,
  selectedOrganizations
}

final class EmailRevocationScope {
  const EmailRevocationScope(
      {required this.mode, this.organizationIds = const []});
  final EmailRevocationScopeMode mode;
  final List<String> organizationIds;
}

enum EmailRevocationReason {
  adminAction,
  compromised,
  incidentResponse,
  offboarding,
  userRequest
}

enum EmailRevocationStatus { completed, partial, denied, noMatch }

/// `normalizedEmail` is write-only and must be discarded after deriving a keyed HMAC.
final class RevokeSessionsByEmailRequest {
  const RevokeSessionsByEmailRequest(
      {required this.requestId,
      required this.idempotencyKey,
      required this.normalizedEmail,
      required this.scope,
      required this.reason,
      required this.dryRun});
  final String requestId;
  final String idempotencyKey;
  final String normalizedEmail;
  final EmailRevocationScope scope;
  final EmailRevocationReason reason;
  final bool dryRun;
}

final class OrganizationRevocationResult {
  const OrganizationRevocationResult(
      {required this.organizationId,
      required this.outcome,
      required this.matchedUsers,
      required this.sessionsRevoked,
      required this.sessionsAlreadyInactive,
      this.errorCode,
      required this.authorizationVerified});
  final String organizationId;
  final String outcome;
  final int matchedUsers;
  final int sessionsRevoked;
  final int sessionsAlreadyInactive;
  final String? errorCode;
  final bool authorizationVerified;
}

/// Sanitized result; an email field and inaccessible organization IDs are intentionally absent.
final class RevokeSessionsByEmailResult {
  const RevokeSessionsByEmailResult(
      {required this.requestId,
      required this.idempotencyKey,
      required this.operationId,
      required this.status,
      required this.replayed,
      required this.dryRun,
      required this.authorizedOrganizationCount,
      required this.unprocessedOrganizationCount,
      required this.matchedUsers,
      required this.sessionsRevoked,
      required this.sessionsAlreadyInactive,
      required this.organizationResults,
      required this.completedAt});
  final String requestId;
  final String idempotencyKey;
  final String operationId;
  final EmailRevocationStatus status;
  final bool replayed;
  final bool dryRun;
  final int authorizedOrganizationCount;
  final int unprocessedOrganizationCount;
  final int matchedUsers;
  final int sessionsRevoked;
  final int sessionsAlreadyInactive;
  final List<OrganizationRevocationResult> organizationResults;
  final String completedAt;
  static const authorizationPolicy = 'per_organization_sessions.revoke';
  static const onlyAuthorizedOrganizationsProcessed = true;
  bool get hasVerifiedAuthorizationBoundary =>
      organizationResults.every((result) => result.authorizationVerified);
}
