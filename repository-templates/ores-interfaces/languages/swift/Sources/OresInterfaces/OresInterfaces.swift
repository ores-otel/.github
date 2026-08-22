import Foundation
public enum AuthMethod: String, Codable, Sendable { case jwt, oidc, webauthn, totp, kerberos, ssh, openpgp, platformBiometric = "platform_biometric", recovery }
public enum AssuranceLevel: String, Codable, Sendable { case aal0, aal1, aal2, aal3 }
public struct PrincipalRef: Codable, Sendable { public let tenantId: String; public let subject: String; public let kind: String; public let organization: String?; public let displayName: String? }
public struct PlatformBiometricProof: Codable, Sendable {
  public let verifiedByPlatformAuthenticator: Bool; public let userVerification: String; public let rawBiometricMaterialPresent: Bool
  public var safe: Bool { verifiedByPlatformAuthenticator && userVerification == "required" && !rawBiometricMaterialPresent }
}
