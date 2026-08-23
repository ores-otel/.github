package com.oresoftware.interfaces;

import java.util.List;

public final class AuthContracts {
  private AuthContracts() {}
  public enum AuthMethod { JWT, OIDC, WEBAUTHN, TOTP, KERBEROS, SSH, OPENPGP, PLATFORM_BIOMETRIC, RECOVERY }
  public enum AssuranceLevel { AAL0, AAL1, AAL2, AAL3 }
  public enum DirectoryAdminScope {
    DASHBOARD_READ("directory.dashboard.read"), USERS_READ("directory.users.read"),
    SESSIONS_READ("directory.sessions.read"), ROLES_READ("directory.roles.read"),
    REVOCATIONS_READ("directory.revocations.read"),
    REVOCATIONS_EXECUTE("directory.revocations.execute");
    private final String wireValue;
    DirectoryAdminScope(String wireValue) { this.wireValue = wireValue; }
    public String wireValue() { return wireValue; }
  }
  public enum DirectoryAdminRole {
    DIRECTORY_ADMIN("directory_admin"),
    DIRECTORY_SECURITY_OPERATOR("directory_security_operator"),
    DIRECTORY_AUDITOR("directory_auditor");
    private final String wireValue;
    DirectoryAdminRole(String wireValue) { this.wireValue = wireValue; }
    public String wireValue() { return wireValue; }
  }
  public enum PrincipalSearchState {
    NO_MATCH("no_match"), UNIQUE("unique"), AMBIGUOUS("ambiguous");
    private final String wireValue;
    PrincipalSearchState(String wireValue) { this.wireValue = wireValue; }
    public String wireValue() { return wireValue; }
  }
  public enum InventoryStatus {
    COMPLETE("complete"), PARTIAL("partial"), UNAVAILABLE("unavailable");
    private final String wireValue;
    InventoryStatus(String wireValue) { this.wireValue = wireValue; }
    public String wireValue() { return wireValue; }
  }
  public enum RevocationScope {
    INTERACTIVE_SESSIONS("interactive_sessions"),
    REFRESH_TOKEN_FAMILIES("refresh_token_families"),
    OFFLINE_GRANTS("offline_grants"),
    DOWNSTREAM_SESSIONS("downstream_sessions"),
    IMPERSONATION_SESSIONS("impersonation_sessions"),
    USER_API_CREDENTIALS("user_api_credentials"),
    REGISTERED_DEVICE_SESSIONS("registered_device_sessions");
    private final String wireValue;
    RevocationScope(String wireValue) { this.wireValue = wireValue; }
    public String wireValue() { return wireValue; }
  }
  public enum RevocationJobState {
    QUEUED("queued", false), RUNNING("running", false), PARTIAL("partial", true),
    SUCCEEDED("succeeded", true), FAILED("failed", true), CANCELLED("cancelled", true);
    private final String wireValue;
    private final boolean terminal;
    RevocationJobState(String wireValue, boolean terminal) { this.wireValue = wireValue; this.terminal = terminal; }
    public String wireValue() { return wireValue; }
    public boolean terminal() { return terminal; }
  }
  public enum RevocationTargetState {
    PENDING("pending"), RUNNING("running"), RETRY_SCHEDULED("retry_scheduled"),
    SUCCEEDED("succeeded"), FAILED("failed"), SKIPPED("skipped"), UNSUPPORTED("unsupported");
    private final String wireValue;
    RevocationTargetState(String wireValue) { this.wireValue = wireValue; }
    public String wireValue() { return wireValue; }
  }
  public record PrincipalRef(String tenantId, String subject, String kind, String organization, String displayName) {}
  public record RequestContext(String requestId, String traceId, String spanId, String tenantId, String clientId, String source) {}
  public record TokenClaims(String issuer, String subject, List<String> audience, long expiresAt, long issuedAt, String tokenId, String tenantId, String sessionId, AssuranceLevel assurance, List<AuthMethod> methods, List<String> scopes) {}
  public record PlatformBiometricProof(boolean verifiedByPlatformAuthenticator, String userVerification, boolean rawBiometricMaterialPresent) {
    public boolean safe() { return verifiedByPlatformAuthenticator && "required".equals(userVerification) && !rawBiometricMaterialPresent; }
  }
  public record RevocationRedaction(boolean rawEmailsPresent, boolean rawTokensPresent, boolean rawSessionIdentifiersPresent, boolean rawBiometricMaterialPresent) {}
  public record ProviderIdentityRef(String providerId, String providerTenantId, String opaqueIdentityHandle) {}
  public record PrincipalSearchRequest(String schema, String requestId, String requestedByPrincipalId, String emailSearchKeyHash, String purpose, String requestedAt, RevocationRedaction redaction) {}
  public record PrincipalSearchCandidate(String principalId, List<ProviderIdentityRef> identities, long organizationCount, long activeSessionCount) {}
  public record PrincipalSearchResult(String schema, String lookupId, String emailSearchKeyHash, PrincipalSearchState state, List<PrincipalSearchCandidate> candidates, boolean requiresExplicitPrincipalSelection, String generatedAt, RevocationRedaction redaction) {}
  public record PrincipalSelectionRequest(String schema, String requestId, String lookupId, String principalId, boolean selectionConfirmed, String requestedAt, RevocationRedaction redaction) {}
  public record PrincipalSelectionResult(String schema, String selectionId, String lookupId, String principalId, String selectedAt, String expiresAt, RevocationRedaction redaction) {}
  public record GlobalRevocationPreviewRequest(String schema, String requestId, String selectionId, List<RevocationScope> selectedScopes, String requestedAt, RevocationRedaction redaction) {}
  public record RevocationBlastRadius(Long providerTenantCount, Long identityCount, Long organizationCount, Long projectCount, Long interactiveSessionCount, Long refreshTokenFamilyCount, Long offlineGrantCount, Long downstreamSessionCount, Long impersonationSessionCount, Long userApiCredentialCount, Long registeredDeviceSessionCount, InventoryStatus inventoryStatus, List<String> unknownFields) {}
  public record RevocationPreviewTarget(String targetIdHash, ProviderIdentityRef identity, RevocationScope scope, long estimatedResourceCount, boolean supported, boolean requiresProviderFanout, Long residualAccessTokenMaxSeconds, List<String> warningCodes) {}
  public record GlobalRevocationPreview(String schema, String previewId, String principalId, String generatedAt, String expiresAt, List<RevocationScope> selectedScopes, RevocationBlastRadius blastRadius, List<RevocationPreviewTarget> targets, boolean ambiguityResolved, boolean requiresStepUp, AssuranceLevel minimumAssurance, boolean phishingResistantStepUpRequired, RevocationRedaction redaction) {}
  public record RevocationStepUp(String actorPrincipalId, String actorSessionIdHash, String evidenceIdHash, AssuranceLevel assurance, List<AuthMethod> authMethods, boolean phishingResistant, String verifiedAt, String freshUntil) {
    public boolean sufficient() { return (assurance == AssuranceLevel.AAL2 || assurance == AssuranceLevel.AAL3) && phishingResistant && authMethods.contains(AuthMethod.WEBAUTHN); }
  }
  public record RevocationRequestCorrelation(String requestId, String traceId, String reasonCode, String ticketReferenceHash) {}
  public record GlobalRevocationRequest(String schema, String previewId, String commitAuthorizationId, String idempotencyKey, List<RevocationScope> selectedScopes, String requestedAt, RevocationRequestCorrelation correlation, RevocationRedaction redaction) {}
  public record GlobalRevocationCommitAuthorization(String schema, String commitAuthorizationId, String previewId, String principalId, List<RevocationScope> selectedScopes, String previewCreatedByPrincipalIdHash, String commitAuthorizedByPrincipalIdHash, String commitAuthorizedBySessionIdHash, boolean dualControlRequired, boolean dualControlSatisfied, RevocationStepUp verifiedStepUp, String issuedAt, String expiresAt, RevocationRedaction redaction) {}
  public record AdminTokenExchangeRedaction(boolean subjectTokenLogged, boolean subjectTokenPersisted, boolean accessTokenLogged, boolean accessTokenPersisted, boolean tokensReturnedInDiagnostics, boolean rawEmailsPresent, boolean rawBiometricMaterialPresent) {}
  public record AdminRevocationTokenExchangeRequest(String schema, String requestId, String subjectToken, String subjectTokenType, String audience, String requestedScope, String requestedAt, AdminTokenExchangeRedaction redaction) {}
  public record AdminRevocationTokenExchangeResult(String schema, String requestId, String accessToken, String issuedTokenType, String tokenType, int expiresInSeconds, String audience, String authorizedParty, String scope, String issuedAt, String expiresAt, AdminTokenExchangeRedaction redaction) {}
  public record RevocationTargetResult(String targetIdHash, ProviderIdentityRef identity, RevocationScope scope, RevocationTargetState state, int attemptCount, boolean retryable, String lastAttemptAt, String nextAttemptAt, Long retryAfterSeconds, String completedAt, String resultCode, String providerRequestIdHash, Long residualAccessTokenMaxSeconds) {}
  public record RevocationFence(String appliedAt, String notBefore, long previousAuthEpoch, long authEpoch, boolean effective) {}
  public record RevocationAuditCorrelation(String auditEventId, String correlationId, String requestId, String traceId, String actorPrincipalId, String actorSessionIdHash, String idempotencyKeyHash, String reasonCode, boolean rawEmailsPresent, boolean rawTokensPresent, boolean rawBiometricMaterialPresent) {}
  public record GlobalRevocationOperation(String schema, String operationId, String principalId, String previewId, RevocationJobState state, List<RevocationScope> selectedScopes, String createdAt, String updatedAt, String completedAt, RevocationFence fence, List<RevocationTargetResult> targets, RevocationAuditCorrelation audit, RevocationRedaction redaction) {}
  public record DirectoryAdminGrant(String grantId, String organizationId, List<String> projectIds, List<DirectoryAdminScope> scopes, List<DirectoryAdminRole> roles, String grantedAt, String expiresAt) {
    public boolean isDirectoryAdmin() { return roles.contains(DirectoryAdminRole.DIRECTORY_ADMIN); }
  }
  public record DirectoryAdminGrantSet(String schema, String principalId, String audience, AssuranceLevel assurance, List<DirectoryAdminGrant> directoryGrants, String evaluatedAt, String expiresAt, boolean exactOrganizationMatchRequired, boolean crossOrganizationFallbackAllowed, boolean rawEmailsPresent) {}
}
