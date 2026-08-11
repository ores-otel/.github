enum AuthMethod { jwt, oidc, webauthn, totp, kerberos, ssh, openpgp, platformBiometric, recovery }
enum AssuranceLevel { aal0, aal1, aal2, aal3 }
final class PrincipalRef {
  const PrincipalRef({required this.tenantId, required this.subject, required this.kind, this.organization, this.displayName});
  final String tenantId; final String subject; final String kind; final String? organization; final String? displayName;
}
final class PlatformBiometricProof {
  const PlatformBiometricProof({required this.verifiedByPlatformAuthenticator, required this.userVerification, this.rawBiometricMaterialPresent = false});
  final bool verifiedByPlatformAuthenticator; final String userVerification; final bool rawBiometricMaterialPresent;
  bool get safe => verifiedByPlatformAuthenticator && userVerification == 'required' && !rawBiometricMaterialPresent;
}

enum ResourceState { active, suspended, archived }
enum UserState { invited, active, suspended, deprovisioned }
enum MembershipState { invited, active, suspended, removed }
enum SessionState { active, revoked, expired }
enum FactorState { pending, active, disabled, compromised }
enum RoleScopeKind { organization, project, repository }

final class Organization {
  const Organization({required this.organizationId, required this.slug, required this.displayName, required this.state, required this.createdAt});
  final String organizationId; final String slug; final String displayName; final ResourceState state; final String createdAt;
}
final class Project {
  const Project({required this.projectId, required this.organizationId, required this.slug, required this.displayName, required this.state, required this.createdAt});
  final String projectId; final String organizationId; final String slug; final String displayName; final ResourceState state; final String createdAt;
}
/// Safe projection: normalized email and its lookup HMAC are deliberately absent.
final class User {
  const User({required this.userId, required this.displayName, required this.emailRedacted, required this.state, required this.createdAt, this.lastAuthenticatedAt});
  final String userId; final String displayName; final String emailRedacted; final UserState state; final String createdAt; final String? lastAuthenticatedAt;
}
final class Membership {
  const Membership({required this.membershipId, required this.organizationId, required this.userId, required this.state, this.joinedAt});
  final String membershipId; final String organizationId; final String userId; final MembershipState state; final String? joinedAt;
}
final class Role {
  const Role({required this.roleId, required this.organizationId, required this.key, required this.displayName, required this.permissions});
  final String roleId; final String organizationId; final String key; final String displayName; final List<String> permissions;
}
final class RoleBinding {
  const RoleBinding({required this.roleBindingId, required this.organizationId, required this.membershipId, required this.roleId, required this.scopeKind, required this.scopeId, required this.grantedAt, this.expiresAt});
  final String roleBindingId; final String organizationId; final String membershipId; final String roleId; final RoleScopeKind scopeKind; final String scopeId; final String grantedAt; final String? expiresAt;
}
/// `sessionIdHash` is a non-reversible display/audit value, never a bearer credential.
final class Session {
  const Session({required this.sessionIdHash, required this.userId, required this.organizationId, this.projectId, required this.clientId, required this.state, required this.assurance, required this.authMethods, required this.createdAt, required this.expiresAt, this.revokedAt});
  final String sessionIdHash; final String userId; final String organizationId; final String? projectId; final String clientId; final SessionState state; final AssuranceLevel assurance; final List<AuthMethod> authMethods; final String createdAt; final String expiresAt; final String? revokedAt;
}
/// Credential metadata only; private keys and biometric material have no representation.
final class Factor {
  const Factor({required this.factorId, required this.userId, required this.method, required this.state, this.externalCredentialRefHash, this.publicKeyFingerprint, this.rawBiometricMaterialPresent = false, this.privateKeyMaterialPresent = false, required this.createdAt, this.lastUsedAt});
  final String factorId; final String userId; final AuthMethod method; final FactorState state; final String? externalCredentialRefHash; final String? publicKeyFingerprint; final bool rawBiometricMaterialPresent; final bool privateKeyMaterialPresent; final String createdAt; final String? lastUsedAt;
  bool get safe => !rawBiometricMaterialPresent && !privateKeyMaterialPresent;
}
final class AuditEvent {
  const AuditEvent({required this.auditEventId, this.organizationId, this.projectId, required this.actorSubject, required this.action, required this.targetKind, required this.targetIdHash, required this.outcome, this.reasonCode, required this.requestId, required this.traceId, required this.occurredAt, this.sensitiveMaterialPresent = false});
  final String auditEventId; final String? organizationId; final String? projectId; final String actorSubject; final String action; final String targetKind; final String targetIdHash; final String outcome; final String? reasonCode; final String requestId; final String traceId; final String occurredAt; final bool sensitiveMaterialPresent;
  bool get safe => !sensitiveMaterialPresent;
}

enum RevocationScopeMode { allAuthorizedOrganizations, selectedOrganizations }
final class RevocationScope {
  const RevocationScope({required this.mode, this.organizationIds = const []});
  final RevocationScopeMode mode; final List<String> organizationIds;
}
enum RevocationReason { adminAction, compromised, incidentResponse, offboarding, userRequest }
enum RevocationStatus { completed, partial, denied, noMatch }
/// `normalizedEmail` is write-only and must be discarded after deriving a keyed HMAC.
final class RevokeSessionsByEmailRequest {
  const RevokeSessionsByEmailRequest({required this.requestId, required this.idempotencyKey, required this.normalizedEmail, required this.scope, required this.reason, required this.dryRun});
  final String requestId; final String idempotencyKey; final String normalizedEmail; final RevocationScope scope; final RevocationReason reason; final bool dryRun;
}
final class OrganizationRevocationResult {
  const OrganizationRevocationResult({required this.organizationId, required this.outcome, required this.matchedUsers, required this.sessionsRevoked, required this.sessionsAlreadyInactive, this.errorCode, required this.authorizationVerified});
  final String organizationId; final String outcome; final int matchedUsers; final int sessionsRevoked; final int sessionsAlreadyInactive; final String? errorCode; final bool authorizationVerified;
}
/// Sanitized result; an email field and inaccessible organization IDs are intentionally absent.
final class RevokeSessionsByEmailResult {
  const RevokeSessionsByEmailResult({required this.requestId, required this.idempotencyKey, required this.operationId, required this.status, required this.replayed, required this.dryRun, required this.authorizedOrganizationCount, required this.unprocessedOrganizationCount, required this.matchedUsers, required this.sessionsRevoked, required this.sessionsAlreadyInactive, required this.organizationResults, required this.completedAt});
  final String requestId; final String idempotencyKey; final String operationId; final RevocationStatus status; final bool replayed; final bool dryRun; final int authorizedOrganizationCount; final int unprocessedOrganizationCount; final int matchedUsers; final int sessionsRevoked; final int sessionsAlreadyInactive; final List<OrganizationRevocationResult> organizationResults; final String completedAt;
  static const authorizationPolicy = 'per_organization_sessions.revoke';
  static const onlyAuthorizedOrganizationsProcessed = true;
  bool get hasVerifiedAuthorizationBoundary => organizationResults.every((result) => result.authorizationVerified);
}
