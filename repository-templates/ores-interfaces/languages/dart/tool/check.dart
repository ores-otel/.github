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
}
