#![forbid(unsafe_code)]

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AuthMethod { Jwt, Oidc, Webauthn, Totp, Kerberos, Ssh, OpenPgp, PlatformBiometric, Recovery }

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum AssuranceLevel { Aal0, Aal1, Aal2, Aal3 }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalKind { Human, Service, Workload, Device, Automation }

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

/// Stable cross-organization Shared Auth records. Date/time fields are RFC 3339 strings on
/// the wire so this foundational crate does not force a time or serialization dependency.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ResourceState { Active, Suspended, Archived }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UserState { Invited, Active, Suspended, Deprovisioned }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MembershipState { Invited, Active, Suspended, Removed }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SessionState { Active, Revoked, Expired }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FactorState { Pending, Active, Disabled, Compromised }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RoleScopeKind { Organization, Project, Repository }

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
    pub fn is_safe(&self) -> bool { !self.sensitive_material_present }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RevocationScope {
    AllAuthorizedOrganizations,
    SelectedOrganizations(Vec<String>),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RevocationReason { AdminAction, Compromised, IncidentResponse, Offboarding, UserRequest }

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RevocationStatus { Completed, Partial, Denied, NoMatch }

/// `normalized_email` is write-only at the transport boundary and must be discarded after
/// deriving the keyed lookup HMAC.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RevokeSessionsByEmailRequest {
    pub request_id: String,
    pub idempotency_key: String,
    pub normalized_email: String,
    pub scope: RevocationScope,
    pub reason: RevocationReason,
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
    pub status: RevocationStatus,
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
            && self.organization_results.iter().all(|result| result.authorization_verified)
    }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn biometric_proof_rejects_raw_material() {
        assert!(PlatformBiometricProof {
            verified_by_platform_authenticator: true,
            user_verification_required: true,
            raw_biometric_material_present: false,
        }.is_safe());
        assert!(!PlatformBiometricProof {
            verified_by_platform_authenticator: true,
            user_verification_required: true,
            raw_biometric_material_present: true,
        }.is_safe());
    }

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
}
