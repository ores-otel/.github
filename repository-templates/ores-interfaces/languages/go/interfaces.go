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
	return p.VerifiedByPlatformAuthenticator &&
		p.UserVerification == "required" &&
		!p.RawBiometricMaterialPresent
}

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
	MembershipID  string          `json:"membershipId"`
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
	RoleBindingID string        `json:"roleBindingId"`
	OrganizationID string        `json:"organizationId"`
	MembershipID  string        `json:"membershipId"`
	RoleID        string        `json:"roleId"`
	ScopeKind     RoleScopeKind `json:"scopeKind"`
	ScopeID       string        `json:"scopeId"`
	GrantedAt     string        `json:"grantedAt"`
	ExpiresAt     string        `json:"expiresAt,omitempty"`
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
	FactorID                     string     `json:"factorId"`
	UserID                       string     `json:"userId"`
	Method                       AuthMethod `json:"method"`
	State                        FactorState `json:"state"`
	ExternalCredentialRefHash    string     `json:"externalCredentialRefHash,omitempty"`
	PublicKeyFingerprint         string     `json:"publicKeyFingerprint,omitempty"`
	RawBiometricMaterialPresent  bool       `json:"rawBiometricMaterialPresent"`
	PrivateKeyMaterialPresent    bool       `json:"privateKeyMaterialPresent"`
	CreatedAt                    string     `json:"createdAt"`
	LastUsedAt                   string     `json:"lastUsedAt,omitempty"`
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

type RevocationScopeMode string

const (
	AllAuthorizedOrganizations RevocationScopeMode = "all_authorized_organizations"
	SelectedOrganizations      RevocationScopeMode = "selected_organizations"
)

type RevocationScope struct {
	Mode            RevocationScopeMode `json:"mode"`
	OrganizationIDs []string            `json:"organizationIds,omitempty"`
}

type RevocationReason string

const (
	RevokeAdminAction      RevocationReason = "admin_action"
	RevokeCompromised      RevocationReason = "compromised"
	RevokeIncidentResponse RevocationReason = "incident_response"
	RevokeOffboarding      RevocationReason = "offboarding"
	RevokeUserRequest      RevocationReason = "user_request"
)

type RevocationStatus string

const (
	RevocationCompleted RevocationStatus = "completed"
	RevocationPartial   RevocationStatus = "partial"
	RevocationDenied    RevocationStatus = "denied"
	RevocationNoMatch   RevocationStatus = "no_match"
)

const AuthorizationPolicyPerOrganization = "per_organization_sessions.revoke"

// RevokeSessionsByEmailRequest.NormalizedEmail is write-only and discarded after HMAC lookup.
type RevokeSessionsByEmailRequest struct {
	RequestID      string           `json:"requestId"`
	IdempotencyKey string           `json:"idempotencyKey"`
	NormalizedEmail string          `json:"normalizedEmail"`
	Scope          RevocationScope  `json:"scope"`
	Reason         RevocationReason `json:"reason"`
	DryRun         bool             `json:"dryRun"`
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
	Status                               RevocationStatus               `json:"status"`
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
