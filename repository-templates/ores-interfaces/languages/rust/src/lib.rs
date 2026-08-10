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
}
