from dataclasses import dataclass
from enum import StrEnum

class AuthMethod(StrEnum):
    JWT="jwt"; OIDC="oidc"; WEBAUTHN="webauthn"; TOTP="totp"; KERBEROS="kerberos"; SSH="ssh"; OPENPGP="openpgp"; PLATFORM_BIOMETRIC="platform_biometric"; RECOVERY="recovery"
class AssuranceLevel(StrEnum):
    AAL0="aal0"; AAL1="aal1"; AAL2="aal2"; AAL3="aal3"
class PrincipalKind(StrEnum):
    HUMAN="human"; SERVICE="service"; WORKLOAD="workload"; DEVICE="device"; AUTOMATION="automation"
@dataclass(frozen=True, slots=True)
class PrincipalRef:
    tenant_id: str; subject: str; kind: PrincipalKind; organization: str | None = None; display_name: str | None = None
@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str; trace_id: str; span_id: str | None = None; tenant_id: str | None = None; client_id: str | None = None; source: str | None = None
@dataclass(frozen=True, slots=True)
class ErrorEnvelope:
    code: str; message: str; retryable: bool; request_id: str
@dataclass(frozen=True, slots=True)
class PlatformBiometricProof:
    verified_by_platform_authenticator: bool; user_verification: str; raw_biometric_material_present: bool = False
    def safe(self) -> bool:
        return self.verified_by_platform_authenticator and self.user_verification == "required" and not self.raw_biometric_material_present
