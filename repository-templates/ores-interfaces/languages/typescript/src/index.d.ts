export type AuthMethod = "jwt" | "oidc" | "webauthn" | "totp" | "kerberos" | "ssh" | "openpgp" | "platform_biometric" | "recovery";
export type AssuranceLevel = "aal0" | "aal1" | "aal2" | "aal3";
export type PrincipalKind = "human" | "service" | "workload" | "device" | "automation";
export interface PrincipalRef { tenantId: string; subject: string; kind: PrincipalKind; organization?: string; displayName?: string; }
export interface RequestContext { requestId: string; traceId: string; spanId?: string; tenantId?: string; clientId?: string; source?: string; }
export interface ErrorEnvelope { code: string; message: string; retryable: boolean; requestId: string; details?: Record<string, unknown>; }
export interface TokenClaims { iss: string; sub: string; aud: string[]; exp: number; iat: number; authTime?: number; jti: string; tenantId: string; sessionId: string; aal: AssuranceLevel; amr: AuthMethod[]; scopes: string[]; }
export interface PlatformBiometricProof { verifiedByPlatformAuthenticator: true; userVerification: "required"; modalityHint?: "face" | "fingerprint" | "unknown"; rawBiometricMaterialPresent: false; }
export declare const AuthMethod: Readonly<Record<string, AuthMethod>>;
export declare const AssuranceLevel: Readonly<Record<string, AssuranceLevel>>;
export declare function isSafePlatformBiometricProof(value: unknown): value is PlatformBiometricProof;
