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
  const stepUp = RevocationStepUp(
    actorPrincipalId: 'principal-operator',
    actorSessionIdHash: 'actor_session_hash_01',
    evidenceIdHash: 'step_up_evidence_hash_01',
    assurance: AssuranceLevel.aal2,
    authMethods: [AuthMethod.webauthn],
    phishingResistant: true,
    verifiedAt: '2026-08-11T15:00:00Z',
    freshUntil: '2026-08-11T15:05:00Z',
  );
  if (!stepUp.sufficient) {
    throw StateError('valid revocation step-up rejected');
  }
  if (!RevocationJobState.partial.terminal ||
      RevocationJobState.running.terminal) {
    throw StateError('revocation terminal-state drift');
  }
  if (RevocationScope.interactiveSessions.wireValue != 'interactive_sessions') {
    throw StateError('revocation scope drift');
  }
  if (DirectoryAdminRole.directoryAdmin.wireValue != 'directory_admin' ||
      DirectoryAdminScope.revocationsExecute.wireValue !=
          'directory.revocations.execute') {
    throw StateError('directory admin contract drift');
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
