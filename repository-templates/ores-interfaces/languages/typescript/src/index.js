export const AuthMethod = Object.freeze({
  JWT: "jwt", OIDC: "oidc", WEBAUTHN: "webauthn", TOTP: "totp",
  KERBEROS: "kerberos", SSH: "ssh", OPENPGP: "openpgp",
  PLATFORM_BIOMETRIC: "platform_biometric", RECOVERY: "recovery"
});
export const AssuranceLevel = Object.freeze({AAL0: "aal0", AAL1: "aal1", AAL2: "aal2", AAL3: "aal3"});
export function isSafePlatformBiometricProof(value) {
  return value?.verifiedByPlatformAuthenticator === true
    && value?.userVerification === "required"
    && value?.rawBiometricMaterialPresent === false;
}
