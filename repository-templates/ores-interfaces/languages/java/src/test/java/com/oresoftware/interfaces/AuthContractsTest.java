package com.oresoftware.interfaces;

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
  }
}
