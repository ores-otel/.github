package com.oresoftware.interfaces;

import java.util.List;

public final class AuthContractsTest {
  private AuthContractsTest() {}
  public static void main(String[] args) {
    var safe = new AuthContracts.PlatformBiometricProof(true, "required", false);
    var unsafe = new AuthContracts.PlatformBiometricProof(true, "required", true);
    if (!safe.safe() || unsafe.safe()) {
      throw new AssertionError("platform biometric proof did not fail closed");
    }
    if (AuthContracts.AuthMethod.values().length != 9) {
      throw new AssertionError("auth method contract drift");
    }
    var stepUp = new AuthContracts.RevocationStepUp(
        "principal-operator", "actor_session_hash_01", "step_up_evidence_hash_01",
        AuthContracts.AssuranceLevel.AAL2, List.of(AuthContracts.AuthMethod.WEBAUTHN),
        true, "2026-08-11T15:00:00Z", "2026-08-11T15:05:00Z");
    if (!stepUp.sufficient()) {
      throw new AssertionError("valid revocation step-up rejected");
    }
    if (!AuthContracts.RevocationJobState.PARTIAL.terminal()
        || AuthContracts.RevocationJobState.RUNNING.terminal()) {
      throw new AssertionError("revocation terminal-state drift");
    }
    if (!"interactive_sessions".equals(AuthContracts.RevocationScope.INTERACTIVE_SESSIONS.wireValue())) {
      throw new AssertionError("revocation scope drift");
    }
    if (!"directory_admin".equals(AuthContracts.DirectoryAdminRole.DIRECTORY_ADMIN.wireValue())
        || !"directory.revocations.execute".equals(
            AuthContracts.DirectoryAdminScope.REVOCATIONS_EXECUTE.wireValue())) {
      throw new AssertionError("directory admin contract drift");
    }
  }
}
