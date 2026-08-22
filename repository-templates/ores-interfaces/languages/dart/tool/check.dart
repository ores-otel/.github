import 'package:ores_interfaces/ores_interfaces.dart';

void main() {
  const safe = PlatformBiometricProof(
    verifiedByPlatformAuthenticator: true,
    userVerification: 'required',
  );
  if (!safe.safe) {
    throw StateError('platform biometric verdict should be safe');
  }
  const unsafe = PlatformBiometricProof(
    verifiedByPlatformAuthenticator: true,
    userVerification: 'required',
    rawBiometricMaterialPresent: true,
  );
  if (unsafe.safe) {
    throw StateError('raw biometric material must fail closed');
  }
  const factor = Factor(
    factorId: 'factor-1',
    userId: 'user-1',
    method: AuthMethod.platformBiometric,
    state: FactorState.active,
    createdAt: '2026-08-11T00:00:00Z',
  );
  if (!factor.safe) {
    throw StateError('metadata-only factor should be safe');
  }
}
