enum AuthMethod { jwt, oidc, webauthn, totp, kerberos, ssh, openpgp, platformBiometric, recovery }
enum AssuranceLevel { aal0, aal1, aal2, aal3 }
final class PrincipalRef {
  const PrincipalRef({required this.tenantId, required this.subject, required this.kind, this.organization, this.displayName});
  final String tenantId; final String subject; final String kind; final String? organization; final String? displayName;
}
final class PlatformBiometricProof {
  const PlatformBiometricProof({required this.verifiedByPlatformAuthenticator, required this.userVerification, this.rawBiometricMaterialPresent = false});
  final bool verifiedByPlatformAuthenticator; final String userVerification; final bool rawBiometricMaterialPresent;
  bool get safe => verifiedByPlatformAuthenticator && userVerification == 'required' && !rawBiometricMaterialPresent;
}
