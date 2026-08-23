package oresinterfaces

type AuthMethod string

const (
	AuthMethodJWT               AuthMethod = "jwt"
	AuthMethodOIDC              AuthMethod = "oidc"
	AuthMethodWebAuthn          AuthMethod = "webauthn"
	AuthMethodTOTP              AuthMethod = "totp"
	AuthMethodKerberos          AuthMethod = "kerberos"
	AuthMethodSSH               AuthMethod = "ssh"
	AuthMethodOpenPGP           AuthMethod = "openpgp"
	AuthMethodPlatformBiometric AuthMethod = "platform_biometric"
	AuthMethodRecovery          AuthMethod = "recovery"
)

type AssuranceLevel string

const (
	Aal0 AssuranceLevel = "aal0"
	Aal1 AssuranceLevel = "aal1"
	Aal2 AssuranceLevel = "aal2"
	Aal3 AssuranceLevel = "aal3"
)

type DirectoryAdminScope string

const (
	DirectoryDashboardRead      DirectoryAdminScope = "directory.dashboard.read"
	DirectoryUsersRead          DirectoryAdminScope = "directory.users.read"
	DirectorySessionsRead       DirectoryAdminScope = "directory.sessions.read"
	DirectoryRolesRead          DirectoryAdminScope = "directory.roles.read"
	DirectoryRevocationsRead    DirectoryAdminScope = "directory.revocations.read"
	DirectoryRevocationsExecute DirectoryAdminScope = "directory.revocations.execute"
)

type DirectoryAdminRole string

const (
	DirectoryAdmin            DirectoryAdminRole = "directory_admin"
	DirectorySecurityOperator DirectoryAdminRole = "directory_security_operator"
	DirectoryAuditor          DirectoryAdminRole = "directory_auditor"
)

type PrincipalSearchState string

const (
	PrincipalSearchNoMatch   PrincipalSearchState = "no_match"
	PrincipalSearchUnique    PrincipalSearchState = "unique"
	PrincipalSearchAmbiguous PrincipalSearchState = "ambiguous"
)

type InventoryStatus string

const (
	InventoryComplete    InventoryStatus = "complete"
	InventoryPartial     InventoryStatus = "partial"
	InventoryUnavailable InventoryStatus = "unavailable"
)

type RevocationScope string

const (
	RevocationInteractiveSessions      RevocationScope = "interactive_sessions"
	RevocationRefreshTokenFamilies     RevocationScope = "refresh_token_families"
	RevocationOfflineGrants            RevocationScope = "offline_grants"
	RevocationDownstreamSessions       RevocationScope = "downstream_sessions"
	RevocationImpersonationSessions    RevocationScope = "impersonation_sessions"
	RevocationUserAPICredentials       RevocationScope = "user_api_credentials"
	RevocationRegisteredDeviceSessions RevocationScope = "registered_device_sessions"
)

type RevocationJobState string

const (
	RevocationQueued    RevocationJobState = "queued"
	RevocationRunning   RevocationJobState = "running"
	RevocationPartial   RevocationJobState = "partial"
	RevocationSucceeded RevocationJobState = "succeeded"
	RevocationFailed    RevocationJobState = "failed"
	RevocationCancelled RevocationJobState = "cancelled"
)

func (s RevocationJobState) Terminal() bool {
	return s == RevocationPartial || s == RevocationSucceeded || s == RevocationFailed || s == RevocationCancelled
}

type RevocationTargetState string

const (
	RevocationTargetPending        RevocationTargetState = "pending"
	RevocationTargetRunning        RevocationTargetState = "running"
	RevocationTargetRetryScheduled RevocationTargetState = "retry_scheduled"
	RevocationTargetSucceeded      RevocationTargetState = "succeeded"
	RevocationTargetFailed         RevocationTargetState = "failed"
	RevocationTargetSkipped        RevocationTargetState = "skipped"
	RevocationTargetUnsupported    RevocationTargetState = "unsupported"
)

type PrincipalRef struct {
	TenantID     string `json:"tenantId"`
	Subject      string `json:"subject"`
	Kind         string `json:"kind"`
	Organization string `json:"organization,omitempty"`
	DisplayName  string `json:"displayName,omitempty"`
}
type RequestContext struct {
	RequestID string `json:"requestId"`
	TraceID   string `json:"traceId"`
	SpanID    string `json:"spanId,omitempty"`
	TenantID  string `json:"tenantId,omitempty"`
	ClientID  string `json:"clientId,omitempty"`
	Source    string `json:"source,omitempty"`
}
type ErrorEnvelope struct {
	Code      string         `json:"code"`
	Message   string         `json:"message"`
	Retryable bool           `json:"retryable"`
	RequestID string         `json:"requestId"`
	Details   map[string]any `json:"details,omitempty"`
}
type PlatformBiometricProof struct {
	VerifiedByPlatformAuthenticator bool   `json:"verifiedByPlatformAuthenticator"`
	UserVerification                string `json:"userVerification"`
	ModalityHint                    string `json:"modalityHint,omitempty"`
	RawBiometricMaterialPresent     bool   `json:"rawBiometricMaterialPresent"`
}

func (p PlatformBiometricProof) Safe() bool {
	return p.VerifiedByPlatformAuthenticator && p.UserVerification == "required" && !p.RawBiometricMaterialPresent
}

type RevocationRedaction struct {
	RawEmailsPresent             bool `json:"rawEmailsPresent"`
	RawTokensPresent             bool `json:"rawTokensPresent"`
	RawSessionIdentifiersPresent bool `json:"rawSessionIdentifiersPresent"`
	RawBiometricMaterialPresent  bool `json:"rawBiometricMaterialPresent"`
}

type ProviderIdentityRef struct {
	ProviderID           string `json:"providerId"`
	ProviderTenantID     string `json:"providerTenantId"`
	OpaqueIdentityHandle string `json:"opaqueIdentityHandle"`
}

type PrincipalSearchRequest struct {
	Schema                 string              `json:"schema"`
	RequestID              string              `json:"requestId"`
	RequestedByPrincipalID string              `json:"requestedByPrincipalId"`
	EmailSearchKeyHash     string              `json:"emailSearchKeyHash"`
	Purpose                string              `json:"purpose"`
	RequestedAt            string              `json:"requestedAt"`
	Redaction              RevocationRedaction `json:"redaction"`
}

type PrincipalSearchCandidate struct {
	PrincipalID        string                `json:"principalId"`
	Identities         []ProviderIdentityRef `json:"identities"`
	OrganizationCount  uint64                `json:"organizationCount"`
	ActiveSessionCount uint64                `json:"activeSessionCount"`
}

type PrincipalSearchResult struct {
	Schema                             string                     `json:"schema"`
	LookupID                           string                     `json:"lookupId"`
	EmailSearchKeyHash                 string                     `json:"emailSearchKeyHash"`
	State                              PrincipalSearchState       `json:"state"`
	Candidates                         []PrincipalSearchCandidate `json:"candidates"`
	RequiresExplicitPrincipalSelection bool                       `json:"requiresExplicitPrincipalSelection"`
	GeneratedAt                        string                     `json:"generatedAt"`
	Redaction                          RevocationRedaction        `json:"redaction"`
}

type PrincipalSelectionRequest struct {
	Schema             string              `json:"schema"`
	RequestID          string              `json:"requestId"`
	LookupID           string              `json:"lookupId"`
	PrincipalID        string              `json:"principalId"`
	SelectionConfirmed bool                `json:"selectionConfirmed"`
	RequestedAt        string              `json:"requestedAt"`
	Redaction          RevocationRedaction `json:"redaction"`
}

type PrincipalSelectionResult struct {
	Schema      string              `json:"schema"`
	SelectionID string              `json:"selectionId"`
	LookupID    string              `json:"lookupId"`
	PrincipalID string              `json:"principalId"`
	SelectedAt  string              `json:"selectedAt"`
	ExpiresAt   string              `json:"expiresAt"`
	Redaction   RevocationRedaction `json:"redaction"`
}

type GlobalRevocationPreviewRequest struct {
	Schema         string              `json:"schema"`
	RequestID      string              `json:"requestId"`
	SelectionID    string              `json:"selectionId"`
	SelectedScopes []RevocationScope   `json:"selectedScopes"`
	RequestedAt    string              `json:"requestedAt"`
	Redaction      RevocationRedaction `json:"redaction"`
}

type RevocationBlastRadius struct {
	ProviderTenantCount          *uint64         `json:"providerTenantCount"`
	IdentityCount                *uint64         `json:"identityCount"`
	OrganizationCount            *uint64         `json:"organizationCount"`
	ProjectCount                 *uint64         `json:"projectCount"`
	InteractiveSessionCount      *uint64         `json:"interactiveSessionCount"`
	RefreshTokenFamilyCount      *uint64         `json:"refreshTokenFamilyCount"`
	OfflineGrantCount            *uint64         `json:"offlineGrantCount"`
	DownstreamSessionCount       *uint64         `json:"downstreamSessionCount"`
	ImpersonationSessionCount    *uint64         `json:"impersonationSessionCount"`
	UserAPICredentialCount       *uint64         `json:"userApiCredentialCount"`
	RegisteredDeviceSessionCount *uint64         `json:"registeredDeviceSessionCount"`
	InventoryStatus              InventoryStatus `json:"inventoryStatus"`
	UnknownFields                []string        `json:"unknownFields"`
}

type RevocationPreviewTarget struct {
	TargetIDHash                  string              `json:"targetIdHash"`
	Identity                      ProviderIdentityRef `json:"identity"`
	Scope                         RevocationScope     `json:"scope"`
	EstimatedResourceCount        uint64              `json:"estimatedResourceCount"`
	Supported                     bool                `json:"supported"`
	RequiresProviderFanout        bool                `json:"requiresProviderFanout"`
	ResidualAccessTokenMaxSeconds *uint64             `json:"residualAccessTokenMaxSeconds"`
	WarningCodes                  []string            `json:"warningCodes"`
}

type GlobalRevocationPreview struct {
	Schema                          string                    `json:"schema"`
	PreviewID                       string                    `json:"previewId"`
	PrincipalID                     string                    `json:"principalId"`
	GeneratedAt                     string                    `json:"generatedAt"`
	ExpiresAt                       string                    `json:"expiresAt"`
	SelectedScopes                  []RevocationScope         `json:"selectedScopes"`
	BlastRadius                     RevocationBlastRadius     `json:"blastRadius"`
	Targets                         []RevocationPreviewTarget `json:"targets"`
	AmbiguityResolved               bool                      `json:"ambiguityResolved"`
	RequiresStepUp                  bool                      `json:"requiresStepUp"`
	MinimumAssurance                AssuranceLevel            `json:"minimumAssurance"`
	PhishingResistantStepUpRequired bool                      `json:"phishingResistantStepUpRequired"`
	Redaction                       RevocationRedaction       `json:"redaction"`
}

type RevocationStepUp struct {
	ActorPrincipalID   string         `json:"actorPrincipalId"`
	ActorSessionIDHash string         `json:"actorSessionIdHash"`
	EvidenceIDHash     string         `json:"evidenceIdHash"`
	Assurance          AssuranceLevel `json:"assurance"`
	AuthMethods        []AuthMethod   `json:"authMethods"`
	PhishingResistant  bool           `json:"phishingResistant"`
	VerifiedAt         string         `json:"verifiedAt"`
	FreshUntil         string         `json:"freshUntil"`
}

func (s RevocationStepUp) Sufficient() bool {
	if (s.Assurance != Aal2 && s.Assurance != Aal3) || !s.PhishingResistant {
		return false
	}
	for _, method := range s.AuthMethods {
		if method == AuthMethodWebAuthn {
			return true
		}
	}
	return false
}

type RevocationRequestCorrelation struct {
	RequestID           string `json:"requestId"`
	TraceID             string `json:"traceId"`
	ReasonCode          string `json:"reasonCode"`
	TicketReferenceHash string `json:"ticketReferenceHash,omitempty"`
}

type GlobalRevocationRequest struct {
	Schema                string                       `json:"schema"`
	PreviewID             string                       `json:"previewId"`
	CommitAuthorizationID string                       `json:"commitAuthorizationId"`
	IdempotencyKey        string                       `json:"idempotencyKey"`
	SelectedScopes        []RevocationScope            `json:"selectedScopes"`
	RequestedAt           string                       `json:"requestedAt"`
	Correlation           RevocationRequestCorrelation `json:"correlation"`
	Redaction             RevocationRedaction          `json:"redaction"`
}

type GlobalRevocationCommitAuthorization struct {
	Schema                            string              `json:"schema"`
	CommitAuthorizationID             string              `json:"commitAuthorizationId"`
	PreviewID                         string              `json:"previewId"`
	PrincipalID                       string              `json:"principalId"`
	SelectedScopes                    []RevocationScope   `json:"selectedScopes"`
	PreviewCreatedByPrincipalIDHash   string              `json:"previewCreatedByPrincipalIdHash"`
	CommitAuthorizedByPrincipalIDHash string              `json:"commitAuthorizedByPrincipalIdHash"`
	CommitAuthorizedBySessionIDHash   string              `json:"commitAuthorizedBySessionIdHash"`
	DualControlRequired               bool                `json:"dualControlRequired"`
	DualControlSatisfied              bool                `json:"dualControlSatisfied"`
	VerifiedStepUp                    RevocationStepUp    `json:"verifiedStepUp"`
	IssuedAt                          string              `json:"issuedAt"`
	ExpiresAt                         string              `json:"expiresAt"`
	Redaction                         RevocationRedaction `json:"redaction"`
}

type AdminTokenExchangeRedaction struct {
	SubjectTokenLogged          bool `json:"subjectTokenLogged"`
	SubjectTokenPersisted       bool `json:"subjectTokenPersisted"`
	AccessTokenLogged           bool `json:"accessTokenLogged"`
	AccessTokenPersisted        bool `json:"accessTokenPersisted"`
	TokensReturnedInDiagnostics bool `json:"tokensReturnedInDiagnostics"`
	RawEmailsPresent            bool `json:"rawEmailsPresent"`
	RawBiometricMaterialPresent bool `json:"rawBiometricMaterialPresent"`
}

type AdminRevocationTokenExchangeRequest struct {
	Schema           string                      `json:"schema"`
	RequestID        string                      `json:"requestId"`
	SubjectToken     string                      `json:"subjectToken"`
	SubjectTokenType string                      `json:"subjectTokenType"`
	Audience         string                      `json:"audience"`
	RequestedScope   string                      `json:"requestedScope"`
	RequestedAt      string                      `json:"requestedAt"`
	Redaction        AdminTokenExchangeRedaction `json:"redaction"`
}

type AdminRevocationTokenExchangeResult struct {
	Schema           string                      `json:"schema"`
	RequestID        string                      `json:"requestId"`
	AccessToken      string                      `json:"accessToken"`
	IssuedTokenType  string                      `json:"issuedTokenType"`
	TokenType        string                      `json:"tokenType"`
	ExpiresInSeconds uint32                      `json:"expiresInSeconds"`
	Audience         string                      `json:"audience"`
	AuthorizedParty  string                      `json:"authorizedParty"`
	Scope            string                      `json:"scope"`
	IssuedAt         string                      `json:"issuedAt"`
	ExpiresAt        string                      `json:"expiresAt"`
	Redaction        AdminTokenExchangeRedaction `json:"redaction"`
}

type RevocationTargetResult struct {
	TargetIDHash                  string                `json:"targetIdHash"`
	Identity                      ProviderIdentityRef   `json:"identity"`
	Scope                         RevocationScope       `json:"scope"`
	State                         RevocationTargetState `json:"state"`
	AttemptCount                  uint32                `json:"attemptCount"`
	Retryable                     bool                  `json:"retryable"`
	LastAttemptAt                 string                `json:"lastAttemptAt,omitempty"`
	NextAttemptAt                 string                `json:"nextAttemptAt,omitempty"`
	RetryAfterSeconds             *uint64               `json:"retryAfterSeconds,omitempty"`
	CompletedAt                   string                `json:"completedAt,omitempty"`
	ResultCode                    string                `json:"resultCode,omitempty"`
	ProviderRequestIDHash         string                `json:"providerRequestIdHash,omitempty"`
	ResidualAccessTokenMaxSeconds *uint64               `json:"residualAccessTokenMaxSeconds"`
}

type RevocationFence struct {
	AppliedAt         string `json:"appliedAt"`
	NotBefore         string `json:"notBefore"`
	PreviousAuthEpoch uint64 `json:"previousAuthEpoch"`
	AuthEpoch         uint64 `json:"authEpoch"`
	Effective         bool   `json:"effective"`
}

type RevocationAuditCorrelation struct {
	AuditEventID                string `json:"auditEventId"`
	CorrelationID               string `json:"correlationId"`
	RequestID                   string `json:"requestId"`
	TraceID                     string `json:"traceId"`
	ActorPrincipalID            string `json:"actorPrincipalId"`
	ActorSessionIDHash          string `json:"actorSessionIdHash"`
	IdempotencyKeyHash          string `json:"idempotencyKeyHash"`
	ReasonCode                  string `json:"reasonCode"`
	RawEmailsPresent            bool   `json:"rawEmailsPresent"`
	RawTokensPresent            bool   `json:"rawTokensPresent"`
	RawBiometricMaterialPresent bool   `json:"rawBiometricMaterialPresent"`
}

type GlobalRevocationOperation struct {
	Schema         string                     `json:"schema"`
	OperationID    string                     `json:"operationId"`
	PrincipalID    string                     `json:"principalId"`
	PreviewID      string                     `json:"previewId"`
	State          RevocationJobState         `json:"state"`
	SelectedScopes []RevocationScope          `json:"selectedScopes"`
	CreatedAt      string                     `json:"createdAt"`
	UpdatedAt      string                     `json:"updatedAt"`
	CompletedAt    string                     `json:"completedAt,omitempty"`
	Fence          RevocationFence            `json:"fence"`
	Targets        []RevocationTargetResult   `json:"targets"`
	Audit          RevocationAuditCorrelation `json:"audit"`
	Redaction      RevocationRedaction        `json:"redaction"`
}

type DirectoryAdminGrant struct {
	GrantID        string                `json:"grantId"`
	OrganizationID string                `json:"organizationId"`
	ProjectIDs     []string              `json:"projectIds,omitempty"`
	Scopes         []DirectoryAdminScope `json:"scopes"`
	Roles          []DirectoryAdminRole  `json:"roles"`
	GrantedAt      string                `json:"grantedAt"`
	ExpiresAt      string                `json:"expiresAt,omitempty"`
}

type DirectoryAdminGrantSet struct {
	Schema                           string                `json:"schema"`
	PrincipalID                      string                `json:"principalId"`
	Audience                         string                `json:"audience"`
	Assurance                        AssuranceLevel        `json:"assurance"`
	DirectoryGrants                  []DirectoryAdminGrant `json:"directoryGrants"`
	EvaluatedAt                      string                `json:"evaluatedAt"`
	ExpiresAt                        string                `json:"expiresAt"`
	ExactOrganizationMatchRequired   bool                  `json:"exactOrganizationMatchRequired"`
	CrossOrganizationFallbackAllowed bool                  `json:"crossOrganizationFallbackAllowed"`
	RawEmailsPresent                 bool                  `json:"rawEmailsPresent"`
}

// Email revocation is a distinct organization-authorized domain from the global control plane.
type ResourceState string

const (
	ResourceActive    ResourceState = "active"
	ResourceSuspended ResourceState = "suspended"
	ResourceArchived  ResourceState = "archived"
)

type UserState string

const (
	UserInvited       UserState = "invited"
	UserActive        UserState = "active"
	UserSuspended     UserState = "suspended"
	UserDeprovisioned UserState = "deprovisioned"
)

type MembershipState string

const (
	MembershipInvited   MembershipState = "invited"
	MembershipActive    MembershipState = "active"
	MembershipSuspended MembershipState = "suspended"
	MembershipRemoved   MembershipState = "removed"
)

type SessionState string

const (
	SessionActive  SessionState = "active"
	SessionRevoked SessionState = "revoked"
	SessionExpired SessionState = "expired"
)

type FactorState string

const (
	FactorPending     FactorState = "pending"
	FactorActive      FactorState = "active"
	FactorDisabled    FactorState = "disabled"
	FactorCompromised FactorState = "compromised"
)

type RoleScopeKind string

const (
	ScopeOrganization RoleScopeKind = "organization"
	ScopeProject      RoleScopeKind = "project"
	ScopeRepository   RoleScopeKind = "repository"
)

type Organization struct {
	OrganizationID string        `json:"organizationId"`
	Slug           string        `json:"slug"`
	DisplayName    string        `json:"displayName"`
	State          ResourceState `json:"state"`
	CreatedAt      string        `json:"createdAt"`
}

type Project struct {
	ProjectID      string        `json:"projectId"`
	OrganizationID string        `json:"organizationId"`
	Slug           string        `json:"slug"`
	DisplayName    string        `json:"displayName"`
	State          ResourceState `json:"state"`
	CreatedAt      string        `json:"createdAt"`
}

// User is a safe projection: neither the normalized address nor lookup HMAC is exposed.
type User struct {
	UserID              string    `json:"userId"`
	DisplayName         string    `json:"displayName"`
	EmailRedacted       string    `json:"emailRedacted"`
	State               UserState `json:"state"`
	CreatedAt           string    `json:"createdAt"`
	LastAuthenticatedAt string    `json:"lastAuthenticatedAt,omitempty"`
}

type Membership struct {
	MembershipID   string          `json:"membershipId"`
	OrganizationID string          `json:"organizationId"`
	UserID         string          `json:"userId"`
	State          MembershipState `json:"state"`
	JoinedAt       string          `json:"joinedAt,omitempty"`
}

type Role struct {
	RoleID         string   `json:"roleId"`
	OrganizationID string   `json:"organizationId"`
	Key            string   `json:"key"`
	DisplayName    string   `json:"displayName"`
	Permissions    []string `json:"permissions"`
}

type RoleBinding struct {
	RoleBindingID  string        `json:"roleBindingId"`
	OrganizationID string        `json:"organizationId"`
	MembershipID   string        `json:"membershipId"`
	RoleID         string        `json:"roleId"`
	ScopeKind      RoleScopeKind `json:"scopeKind"`
	ScopeID        string        `json:"scopeId"`
	GrantedAt      string        `json:"grantedAt"`
	ExpiresAt      string        `json:"expiresAt,omitempty"`
}

// Session exposes only a non-reversible display/audit hash, never a bearer identifier.
type Session struct {
	SessionIDHash  string         `json:"sessionIdHash"`
	UserID         string         `json:"userId"`
	OrganizationID string         `json:"organizationId"`
	ProjectID      string         `json:"projectId,omitempty"`
	ClientID       string         `json:"clientId"`
	State          SessionState   `json:"state"`
	Assurance      AssuranceLevel `json:"assurance"`
	AuthMethods    []AuthMethod   `json:"authMethods"`
	CreatedAt      string         `json:"createdAt"`
	ExpiresAt      string         `json:"expiresAt"`
	RevokedAt      string         `json:"revokedAt,omitempty"`
}

// Factor is metadata only. Private keys and biometric material have no representation.
type Factor struct {
	FactorID                    string      `json:"factorId"`
	UserID                      string      `json:"userId"`
	Method                      AuthMethod  `json:"method"`
	State                       FactorState `json:"state"`
	ExternalCredentialRefHash   string      `json:"externalCredentialRefHash,omitempty"`
	PublicKeyFingerprint        string      `json:"publicKeyFingerprint,omitempty"`
	RawBiometricMaterialPresent bool        `json:"rawBiometricMaterialPresent"`
	PrivateKeyMaterialPresent   bool        `json:"privateKeyMaterialPresent"`
	CreatedAt                   string      `json:"createdAt"`
	LastUsedAt                  string      `json:"lastUsedAt,omitempty"`
}

func (f Factor) Safe() bool {
	return !f.RawBiometricMaterialPresent && !f.PrivateKeyMaterialPresent
}

type AuditEvent struct {
	AuditEventID             string `json:"auditEventId"`
	OrganizationID           string `json:"organizationId,omitempty"`
	ProjectID                string `json:"projectId,omitempty"`
	ActorSubject             string `json:"actorSubject"`
	Action                   string `json:"action"`
	TargetKind               string `json:"targetKind"`
	TargetIDHash             string `json:"targetIdHash"`
	Outcome                  string `json:"outcome"`
	ReasonCode               string `json:"reasonCode,omitempty"`
	RequestID                string `json:"requestId"`
	TraceID                  string `json:"traceId"`
	OccurredAt               string `json:"occurredAt"`
	SensitiveMaterialPresent bool   `json:"sensitiveMaterialPresent"`
}

type EmailRevocationScopeMode string

const (
	AllAuthorizedOrganizations EmailRevocationScopeMode = "all_authorized_organizations"
	SelectedOrganizations      EmailRevocationScopeMode = "selected_organizations"
)

type EmailRevocationScope struct {
	Mode            EmailRevocationScopeMode `json:"mode"`
	OrganizationIDs []string                 `json:"organizationIds,omitempty"`
}

type EmailRevocationReason string

const (
	RevokeAdminAction      EmailRevocationReason = "admin_action"
	RevokeCompromised      EmailRevocationReason = "compromised"
	RevokeIncidentResponse EmailRevocationReason = "incident_response"
	RevokeOffboarding      EmailRevocationReason = "offboarding"
	RevokeUserRequest      EmailRevocationReason = "user_request"
)

type EmailRevocationStatus string

const (
	EmailRevocationCompleted EmailRevocationStatus = "completed"
	EmailRevocationPartial   EmailRevocationStatus = "partial"
	EmailRevocationDenied    EmailRevocationStatus = "denied"
	EmailRevocationNoMatch   EmailRevocationStatus = "no_match"
)

const AuthorizationPolicyPerOrganization = "per_organization_sessions.revoke"

// RevokeSessionsByEmailRequest.NormalizedEmail is write-only and discarded after HMAC lookup.
type RevokeSessionsByEmailRequest struct {
	RequestID       string                `json:"requestId"`
	IdempotencyKey  string                `json:"idempotencyKey"`
	NormalizedEmail string                `json:"normalizedEmail"`
	Scope           EmailRevocationScope  `json:"scope"`
	Reason          EmailRevocationReason `json:"reason"`
	DryRun          bool                  `json:"dryRun"`
}

type OrganizationRevocationResult struct {
	OrganizationID          string `json:"organizationId"`
	Outcome                 string `json:"outcome"`
	MatchedUsers            uint64 `json:"matchedUsers"`
	SessionsRevoked         uint64 `json:"sessionsRevoked"`
	SessionsAlreadyInactive uint64 `json:"sessionsAlreadyInactive"`
	ErrorCode               string `json:"errorCode,omitempty"`
	AuthorizationVerified   bool   `json:"authorizationVerified"`
}

// RevokeSessionsByEmailResult cannot echo the address or inaccessible organization identities.
type RevokeSessionsByEmailResult struct {
	RequestID                            string                         `json:"requestId"`
	IdempotencyKey                       string                         `json:"idempotencyKey"`
	OperationID                          string                         `json:"operationId"`
	Status                               EmailRevocationStatus          `json:"status"`
	Replayed                             bool                           `json:"replayed"`
	DryRun                               bool                           `json:"dryRun"`
	AuthorizedOrganizationCount          uint64                         `json:"authorizedOrganizationCount"`
	UnprocessedOrganizationCount         uint64                         `json:"unprocessedOrganizationCount"`
	MatchedUsers                         uint64                         `json:"matchedUsers"`
	SessionsRevoked                      uint64                         `json:"sessionsRevoked"`
	SessionsAlreadyInactive              uint64                         `json:"sessionsAlreadyInactive"`
	OrganizationResults                  []OrganizationRevocationResult `json:"organizationResults"`
	AuthorizationPolicy                  string                         `json:"authorizationPolicy"`
	OnlyAuthorizedOrganizationsProcessed bool                           `json:"onlyAuthorizedOrganizationsProcessed"`
	CompletedAt                          string                         `json:"completedAt"`
}

func (r RevokeSessionsByEmailResult) HasVerifiedAuthorizationBoundary() bool {
	if r.AuthorizationPolicy != AuthorizationPolicyPerOrganization ||
		!r.OnlyAuthorizedOrganizationsProcessed {
		return false
	}
	for _, result := range r.OrganizationResults {
		if !result.AuthorizationVerified {
			return false
		}
	}
	return true
}
