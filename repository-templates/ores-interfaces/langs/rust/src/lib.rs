#![forbid(unsafe_code)]

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AuthMethod {
    Jwt,
    Oidc,
    Webauthn,
    Totp,
    Kerberos,
    Ssh,
    OpenPgp,
    PlatformBiometric,
    Recovery,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum AssuranceLevel {
    Aal0,
    Aal1,
    Aal2,
    Aal3,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DirectoryAdminScope {
    DashboardRead,
    UsersRead,
    SessionsRead,
    RolesRead,
    RevocationsRead,
    RevocationsExecute,
}

impl DirectoryAdminScope {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::DashboardRead => "directory.dashboard.read",
            Self::UsersRead => "directory.users.read",
            Self::SessionsRead => "directory.sessions.read",
            Self::RolesRead => "directory.roles.read",
            Self::RevocationsRead => "directory.revocations.read",
            Self::RevocationsExecute => "directory.revocations.execute",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DirectoryAdminRole {
    DirectoryAdmin,
    DirectorySecurityOperator,
    DirectoryAuditor,
}

impl DirectoryAdminRole {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::DirectoryAdmin => "directory_admin",
            Self::DirectorySecurityOperator => "directory_security_operator",
            Self::DirectoryAuditor => "directory_auditor",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalSearchState {
    NoMatch,
    Unique,
    Ambiguous,
}

impl PrincipalSearchState {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::NoMatch => "no_match",
            Self::Unique => "unique",
            Self::Ambiguous => "ambiguous",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum InventoryStatus {
    Complete,
    Partial,
    Unavailable,
}

impl InventoryStatus {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Complete => "complete",
            Self::Partial => "partial",
            Self::Unavailable => "unavailable",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RevocationScope {
    InteractiveSessions,
    RefreshTokenFamilies,
    OfflineGrants,
    DownstreamSessions,
    ImpersonationSessions,
    UserApiCredentials,
    RegisteredDeviceSessions,
}

impl RevocationScope {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::InteractiveSessions => "interactive_sessions",
            Self::RefreshTokenFamilies => "refresh_token_families",
            Self::OfflineGrants => "offline_grants",
            Self::DownstreamSessions => "downstream_sessions",
            Self::ImpersonationSessions => "impersonation_sessions",
            Self::UserApiCredentials => "user_api_credentials",
            Self::RegisteredDeviceSessions => "registered_device_sessions",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RevocationJobState {
    Queued,
    Running,
    Partial,
    Succeeded,
    Failed,
    Cancelled,
}

impl RevocationJobState {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Queued => "queued",
            Self::Running => "running",
            Self::Partial => "partial",
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
            Self::Cancelled => "cancelled",
        }
    }

    pub fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Partial | Self::Succeeded | Self::Failed | Self::Cancelled
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RevocationTargetState {
    Pending,
    Running,
    RetryScheduled,
    Succeeded,
    Failed,
    Skipped,
    Unsupported,
}

impl RevocationTargetState {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Pending => "pending",
            Self::Running => "running",
            Self::RetryScheduled => "retry_scheduled",
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
            Self::Skipped => "skipped",
            Self::Unsupported => "unsupported",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalKind {
    Human,
    Service,
    Workload,
    Device,
    Automation,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalRef {
    pub tenant_id: String,
    pub subject: String,
    pub kind: PrincipalKind,
    pub organization: Option<String>,
    pub display_name: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RequestContext {
    pub request_id: String,
    pub trace_id: String,
    pub span_id: Option<String>,
    pub tenant_id: Option<String>,
    pub client_id: Option<String>,
    pub source: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ErrorEnvelope {
    pub code: String,
    pub message: String,
    pub retryable: bool,
    pub request_id: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TokenClaims {
    pub issuer: String,
    pub subject: String,
    pub audience: Vec<String>,
    pub expires_at: u64,
    pub issued_at: u64,
    pub auth_time: Option<u64>,
    pub token_id: String,
    pub tenant_id: String,
    pub session_id: String,
    pub assurance: AssuranceLevel,
    pub methods: Vec<AuthMethod>,
    pub scopes: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PlatformBiometricProof {
    pub verified_by_platform_authenticator: bool,
    pub user_verification_required: bool,
    pub raw_biometric_material_present: bool,
}

impl PlatformBiometricProof {
    pub fn is_safe(&self) -> bool {
        self.verified_by_platform_authenticator
            && self.user_verification_required
            && !self.raw_biometric_material_present
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationRedaction {
    pub raw_emails_present: bool,
    pub raw_tokens_present: bool,
    pub raw_session_identifiers_present: bool,
    pub raw_biometric_material_present: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProviderIdentityRef {
    pub provider_id: String,
    pub provider_tenant_id: String,
    pub opaque_identity_handle: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalSearchRequest {
    pub schema: String,
    pub request_id: String,
    pub requested_by_principal_id: String,
    pub email_search_key_hash: String,
    pub purpose: String,
    pub requested_at: String,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalSearchCandidate {
    pub principal_id: String,
    pub identities: Vec<ProviderIdentityRef>,
    pub organization_count: u64,
    pub active_session_count: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalSearchResult {
    pub schema: String,
    pub lookup_id: String,
    pub email_search_key_hash: String,
    pub state: PrincipalSearchState,
    pub candidates: Vec<PrincipalSearchCandidate>,
    pub requires_explicit_principal_selection: bool,
    pub generated_at: String,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalSelectionRequest {
    pub schema: String,
    pub request_id: String,
    pub lookup_id: String,
    pub principal_id: String,
    pub selection_confirmed: bool,
    pub requested_at: String,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalSelectionResult {
    pub schema: String,
    pub selection_id: String,
    pub lookup_id: String,
    pub principal_id: String,
    pub selected_at: String,
    pub expires_at: String,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlobalRevocationPreviewRequest {
    pub schema: String,
    pub request_id: String,
    pub selection_id: String,
    pub selected_scopes: Vec<RevocationScope>,
    pub requested_at: String,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationBlastRadius {
    pub provider_tenant_count: Option<u64>,
    pub identity_count: Option<u64>,
    pub organization_count: Option<u64>,
    pub project_count: Option<u64>,
    pub interactive_session_count: Option<u64>,
    pub refresh_token_family_count: Option<u64>,
    pub offline_grant_count: Option<u64>,
    pub downstream_session_count: Option<u64>,
    pub impersonation_session_count: Option<u64>,
    pub user_api_credential_count: Option<u64>,
    pub registered_device_session_count: Option<u64>,
    pub inventory_status: InventoryStatus,
    pub unknown_fields: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationPreviewTarget {
    pub target_id_hash: String,
    pub identity: ProviderIdentityRef,
    pub scope: RevocationScope,
    pub estimated_resource_count: u64,
    pub supported: bool,
    pub requires_provider_fanout: bool,
    pub residual_access_token_max_seconds: Option<u64>,
    pub warning_codes: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlobalRevocationPreview {
    pub schema: String,
    pub preview_id: String,
    pub principal_id: String,
    pub generated_at: String,
    pub expires_at: String,
    pub selected_scopes: Vec<RevocationScope>,
    pub blast_radius: RevocationBlastRadius,
    pub targets: Vec<RevocationPreviewTarget>,
    pub ambiguity_resolved: bool,
    pub requires_step_up: bool,
    pub minimum_assurance: AssuranceLevel,
    pub phishing_resistant_step_up_required: bool,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationStepUp {
    pub actor_principal_id: String,
    pub actor_session_id_hash: String,
    pub evidence_id_hash: String,
    pub assurance: AssuranceLevel,
    pub auth_methods: Vec<AuthMethod>,
    pub phishing_resistant: bool,
    pub verified_at: String,
    pub fresh_until: String,
}

impl RevocationStepUp {
    pub fn is_sufficient(&self) -> bool {
        self.assurance >= AssuranceLevel::Aal2
            && self.phishing_resistant
            && self.auth_methods.contains(&AuthMethod::Webauthn)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationRequestCorrelation {
    pub request_id: String,
    pub trace_id: String,
    pub reason_code: String,
    pub ticket_reference_hash: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlobalRevocationRequest {
    pub schema: String,
    pub preview_id: String,
    pub commit_authorization_id: String,
    pub idempotency_key: String,
    pub selected_scopes: Vec<RevocationScope>,
    pub requested_at: String,
    pub correlation: RevocationRequestCorrelation,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlobalRevocationCommitAuthorization {
    pub schema: String,
    pub commit_authorization_id: String,
    pub preview_id: String,
    pub principal_id: String,
    pub selected_scopes: Vec<RevocationScope>,
    pub preview_created_by_principal_id_hash: String,
    pub commit_authorized_by_principal_id_hash: String,
    pub commit_authorized_by_session_id_hash: String,
    pub dual_control_required: bool,
    pub dual_control_satisfied: bool,
    pub verified_step_up: RevocationStepUp,
    pub issued_at: String,
    pub expires_at: String,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdminTokenExchangeRedaction {
    pub subject_token_logged: bool,
    pub subject_token_persisted: bool,
    pub access_token_logged: bool,
    pub access_token_persisted: bool,
    pub tokens_returned_in_diagnostics: bool,
    pub raw_emails_present: bool,
    pub raw_biometric_material_present: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdminRevocationTokenExchangeRequest {
    pub schema: String,
    pub request_id: String,
    pub subject_token: String,
    pub subject_token_type: String,
    pub audience: String,
    pub requested_scope: String,
    pub requested_at: String,
    pub redaction: AdminTokenExchangeRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdminRevocationTokenExchangeResult {
    pub schema: String,
    pub request_id: String,
    pub access_token: String,
    pub issued_token_type: String,
    pub token_type: String,
    pub expires_in_seconds: u32,
    pub audience: String,
    pub authorized_party: String,
    pub scope: String,
    pub issued_at: String,
    pub expires_at: String,
    pub redaction: AdminTokenExchangeRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationTargetResult {
    pub target_id_hash: String,
    pub identity: ProviderIdentityRef,
    pub scope: RevocationScope,
    pub state: RevocationTargetState,
    pub attempt_count: u32,
    pub retryable: bool,
    pub last_attempt_at: Option<String>,
    pub next_attempt_at: Option<String>,
    pub retry_after_seconds: Option<u64>,
    pub completed_at: Option<String>,
    pub result_code: Option<String>,
    pub provider_request_id_hash: Option<String>,
    pub residual_access_token_max_seconds: Option<u64>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationFence {
    pub applied_at: String,
    pub not_before: String,
    pub previous_auth_epoch: u64,
    pub auth_epoch: u64,
    pub effective: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevocationAuditCorrelation {
    pub audit_event_id: String,
    pub correlation_id: String,
    pub request_id: String,
    pub trace_id: String,
    pub actor_principal_id: String,
    pub actor_session_id_hash: String,
    pub idempotency_key_hash: String,
    pub reason_code: String,
    pub raw_emails_present: bool,
    pub raw_tokens_present: bool,
    pub raw_biometric_material_present: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlobalRevocationOperation {
    pub schema: String,
    pub operation_id: String,
    pub principal_id: String,
    pub preview_id: String,
    pub state: RevocationJobState,
    pub selected_scopes: Vec<RevocationScope>,
    pub created_at: String,
    pub updated_at: String,
    pub completed_at: Option<String>,
    pub fence: RevocationFence,
    pub targets: Vec<RevocationTargetResult>,
    pub audit: RevocationAuditCorrelation,
    pub redaction: RevocationRedaction,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DirectoryAdminGrant {
    pub grant_id: String,
    pub organization_id: String,
    pub project_ids: Option<Vec<String>>,
    pub scopes: Vec<DirectoryAdminScope>,
    pub roles: Vec<DirectoryAdminRole>,
    pub granted_at: String,
    pub expires_at: Option<String>,
}

impl DirectoryAdminGrant {
    pub fn is_directory_admin(&self) -> bool {
        self.roles.contains(&DirectoryAdminRole::DirectoryAdmin)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DirectoryAdminGrantSet {
    pub schema: String,
    pub principal_id: String,
    pub audience: String,
    pub assurance: AssuranceLevel,
    pub directory_grants: Vec<DirectoryAdminGrant>,
    pub evaluated_at: String,
    pub expires_at: String,
    pub exact_organization_match_required: bool,
    pub cross_organization_fallback_allowed: bool,
    pub raw_emails_present: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceState {
    Active,
    Suspended,
    Archived,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UserState {
    Invited,
    Active,
    Suspended,
    Deprovisioned,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MembershipState {
    Invited,
    Active,
    Suspended,
    Removed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SessionState {
    Active,
    Revoked,
    Expired,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FactorState {
    Pending,
    Active,
    Disabled,
    Compromised,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RoleScopeKind {
    Organization,
    Project,
    Repository,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Organization {
    pub organization_id: String,
    pub slug: String,
    pub display_name: String,
    pub state: ResourceState,
    pub created_at: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Project {
    pub project_id: String,
    pub organization_id: String,
    pub slug: String,
    pub display_name: String,
    pub state: ResourceState,
    pub created_at: String,
}

/// Safe user projection: the normalized address and lookup HMAC are intentionally absent.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct User {
    pub user_id: String,
    pub display_name: String,
    pub email_redacted: String,
    pub state: UserState,
    pub created_at: String,
    pub last_authenticated_at: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Membership {
    pub membership_id: String,
    pub organization_id: String,
    pub user_id: String,
    pub state: MembershipState,
    pub joined_at: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Role {
    pub role_id: String,
    pub organization_id: String,
    pub key: String,
    pub display_name: String,
    pub permissions: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RoleBinding {
    pub role_binding_id: String,
    pub organization_id: String,
    pub membership_id: String,
    pub role_id: String,
    pub scope_kind: RoleScopeKind,
    pub scope_id: String,
    pub granted_at: String,
    pub expires_at: Option<String>,
}

/// A display/audit projection. `session_id_hash` is never a usable session identifier.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Session {
    pub session_id_hash: String,
    pub user_id: String,
    pub organization_id: String,
    pub project_id: Option<String>,
    pub client_id: String,
    pub state: SessionState,
    pub assurance: AssuranceLevel,
    pub auth_methods: Vec<AuthMethod>,
    pub created_at: String,
    pub expires_at: String,
    pub revoked_at: Option<String>,
}

/// Credential metadata only; neither private keys nor biometric material have a field.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Factor {
    pub factor_id: String,
    pub user_id: String,
    pub method: AuthMethod,
    pub state: FactorState,
    pub external_credential_ref_hash: Option<String>,
    pub public_key_fingerprint: Option<String>,
    pub raw_biometric_material_present: bool,
    pub private_key_material_present: bool,
    pub created_at: String,
    pub last_used_at: Option<String>,
}

impl Factor {
    pub fn is_safe(&self) -> bool {
        !self.raw_biometric_material_present && !self.private_key_material_present
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AuditEvent {
    pub audit_event_id: String,
    pub organization_id: Option<String>,
    pub project_id: Option<String>,
    pub actor_subject: String,
    pub action: String,
    pub target_kind: String,
    pub target_id_hash: String,
    pub outcome: String,
    pub reason_code: Option<String>,
    pub request_id: String,
    pub trace_id: String,
    pub occurred_at: String,
    pub sensitive_material_present: bool,
}

impl AuditEvent {
    pub fn is_safe(&self) -> bool {
        !self.sensitive_material_present
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EmailRevocationScope {
    AllAuthorizedOrganizations,
    SelectedOrganizations(Vec<String>),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EmailRevocationReason {
    AdminAction,
    Compromised,
    IncidentResponse,
    Offboarding,
    UserRequest,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EmailRevocationStatus {
    Completed,
    Partial,
    Denied,
    NoMatch,
}

/// `normalized_email` is write-only at the transport boundary and must be discarded after
/// deriving the keyed lookup HMAC.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevokeSessionsByEmailRequest {
    pub request_id: String,
    pub idempotency_key: String,
    pub normalized_email: String,
    pub scope: EmailRevocationScope,
    pub reason: EmailRevocationReason,
    pub dry_run: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OrganizationRevocationResult {
    pub organization_id: String,
    pub outcome: String,
    pub matched_users: u64,
    pub sessions_revoked: u64,
    pub sessions_already_inactive: u64,
    pub error_code: Option<String>,
    pub authorization_verified: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevokeSessionsByEmailResult {
    pub request_id: String,
    pub idempotency_key: String,
    pub operation_id: String,
    pub status: EmailRevocationStatus,
    pub replayed: bool,
    pub dry_run: bool,
    pub authorized_organization_count: u64,
    pub unprocessed_organization_count: u64,
    pub matched_users: u64,
    pub sessions_revoked: u64,
    pub sessions_already_inactive: u64,
    pub organization_results: Vec<OrganizationRevocationResult>,
    pub authorization_policy: String,
    pub only_authorized_organizations_processed: bool,
    pub completed_at: String,
}

impl RevokeSessionsByEmailResult {
    pub fn has_verified_authorization_boundary(&self) -> bool {
        self.authorization_policy == "per_organization_sessions.revoke"
            && self.only_authorized_organizations_processed
            && self
                .organization_results
                .iter()
                .all(|result| result.authorization_verified)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn biometric_proof_rejects_raw_material() {
        assert!(PlatformBiometricProof {
            verified_by_platform_authenticator: true,
            user_verification_required: true,
            raw_biometric_material_present: false,
        }
        .is_safe());
        assert!(!PlatformBiometricProof {
            verified_by_platform_authenticator: true,
            user_verification_required: true,
            raw_biometric_material_present: true,
        }
        .is_safe());
    }

    #[test]
    fn revocation_requires_phishing_resistant_aal2_webauthn() {
        let valid = RevocationStepUp {
            actor_principal_id: "principal-operator".into(),
            actor_session_id_hash: "actor_session_hash_01".into(),
            evidence_id_hash: "step_up_evidence_hash_01".into(),
            assurance: AssuranceLevel::Aal2,
            auth_methods: vec![AuthMethod::Webauthn],
            phishing_resistant: true,
            verified_at: "2026-08-11T15:00:00Z".into(),
            fresh_until: "2026-08-11T15:05:00Z".into(),
        };
        assert!(valid.is_sufficient());

        let mut insufficient = valid.clone();
        insufficient.assurance = AssuranceLevel::Aal1;
        assert!(!insufficient.is_sufficient());
    }

    #[test]
    fn partial_revocation_is_an_honest_terminal_state() {
        assert!(RevocationJobState::Partial.is_terminal());
        assert!(!RevocationJobState::Running.is_terminal());
        assert_eq!(
            RevocationScope::InteractiveSessions.as_str(),
            "interactive_sessions"
        );
        assert_eq!(InventoryStatus::Unavailable.as_str(), "unavailable");
    }

    #[test]
    fn directory_admin_values_are_exact() {
        assert_eq!(
            DirectoryAdminRole::DirectoryAdmin.as_str(),
            "directory_admin"
        );
        assert_eq!(
            DirectoryAdminScope::RevocationsExecute.as_str(),
            "directory.revocations.execute"
        );
    }
}

#[cfg(test)]
mod email_revocation_domain_tests {
    use super::*;

    #[test]
    fn factor_rejects_forbidden_material_flags() {
        let mut factor = Factor {
            factor_id: "factor-1".into(),
            user_id: "user-1".into(),
            method: AuthMethod::PlatformBiometric,
            state: FactorState::Active,
            external_credential_ref_hash: None,
            public_key_fingerprint: None,
            raw_biometric_material_present: false,
            private_key_material_present: false,
            created_at: "2026-08-11T00:00:00Z".into(),
            last_used_at: None,
        };
        assert!(factor.is_safe());
        factor.raw_biometric_material_present = true;
        assert!(!factor.is_safe());
    }

    #[test]
    fn email_revocation_result_requires_every_authorization_boundary() {
        let result = RevokeSessionsByEmailResult {
            request_id: "request-1".into(),
            idempotency_key: "idempotency-key-1".into(),
            operation_id: "operation-1".into(),
            status: EmailRevocationStatus::Completed,
            replayed: false,
            dry_run: false,
            authorized_organization_count: 1,
            unprocessed_organization_count: 0,
            matched_users: 1,
            sessions_revoked: 1,
            sessions_already_inactive: 0,
            organization_results: vec![OrganizationRevocationResult {
                organization_id: "organization-1".into(),
                outcome: "revoked".into(),
                matched_users: 1,
                sessions_revoked: 1,
                sessions_already_inactive: 0,
                error_code: None,
                authorization_verified: true,
            }],
            authorization_policy: "per_organization_sessions.revoke".into(),
            only_authorized_organizations_processed: true,
            completed_at: "2026-08-11T00:00:00Z".into(),
        };
        assert!(result.has_verified_authorization_boundary());
    }
}
