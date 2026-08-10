package com.oresoftware.interfaces;

import java.util.List;

public final class AuthContracts {
  private AuthContracts() {}
  public enum AuthMethod { JWT, OIDC, WEBAUTHN, TOTP, KERBEROS, SSH, OPENPGP, PLATFORM_BIOMETRIC, RECOVERY }
  public enum AssuranceLevel { AAL0, AAL1, AAL2, AAL3 }
  public record PrincipalRef(String tenantId, String subject, String kind, String organization, String displayName) {}
  public record RequestContext(String requestId, String traceId, String spanId, String tenantId, String clientId, String source) {}
  public record TokenClaims(String issuer, String subject, List<String> audience, long expiresAt, long issuedAt, String tokenId, String tenantId, String sessionId, AssuranceLevel assurance, List<AuthMethod> methods, List<String> scopes) {}
  public record PlatformBiometricProof(boolean verifiedByPlatformAuthenticator, String userVerification, boolean rawBiometricMaterialPresent) {
    public boolean safe() { return verifiedByPlatformAuthenticator && "required".equals(userVerification) && !rawBiometricMaterialPresent; }
  }
}
