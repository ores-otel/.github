package oresinterfaces

type AuthMethod string
const (
    AuthMethodJWT AuthMethod = "jwt"
    AuthMethodOIDC AuthMethod = "oidc"
    AuthMethodWebAuthn AuthMethod = "webauthn"
    AuthMethodTOTP AuthMethod = "totp"
    AuthMethodKerberos AuthMethod = "kerberos"
    AuthMethodSSH AuthMethod = "ssh"
    AuthMethodOpenPGP AuthMethod = "openpgp"
    AuthMethodPlatformBiometric AuthMethod = "platform_biometric"
    AuthMethodRecovery AuthMethod = "recovery"
)

type AssuranceLevel string
const ( Aal0 AssuranceLevel = "aal0"; Aal1 AssuranceLevel = "aal1"; Aal2 AssuranceLevel = "aal2"; Aal3 AssuranceLevel = "aal3" )

type PrincipalRef struct { TenantID string `json:"tenantId"`; Subject string `json:"subject"`; Kind string `json:"kind"`; Organization string `json:"organization,omitempty"`; DisplayName string `json:"displayName,omitempty"` }
type RequestContext struct { RequestID string `json:"requestId"`; TraceID string `json:"traceId"`; SpanID string `json:"spanId,omitempty"`; TenantID string `json:"tenantId,omitempty"`; ClientID string `json:"clientId,omitempty"`; Source string `json:"source,omitempty"` }
type ErrorEnvelope struct { Code string `json:"code"`; Message string `json:"message"`; Retryable bool `json:"retryable"`; RequestID string `json:"requestId"`; Details map[string]any `json:"details,omitempty"` }
type PlatformBiometricProof struct { VerifiedByPlatformAuthenticator bool `json:"verifiedByPlatformAuthenticator"`; UserVerification string `json:"userVerification"`; ModalityHint string `json:"modalityHint,omitempty"`; RawBiometricMaterialPresent bool `json:"rawBiometricMaterialPresent"` }
func (p PlatformBiometricProof) Safe() bool { return p.VerifiedByPlatformAuthenticator && p.UserVerification == "required" && !p.RawBiometricMaterialPresent }
