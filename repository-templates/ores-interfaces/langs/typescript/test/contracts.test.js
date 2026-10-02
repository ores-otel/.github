import test from "node:test";
import assert from "node:assert/strict";
import {
  AuthMethod,
  DirectoryAdminRole,
  DirectoryAdminScope,
  InventoryStatus,
  RevocationJobState,
  RevocationScope,
  isSafePlatformBiometricProof,
  isSufficientRevocationStepUp,
  isTerminalRevocationJobState,
} from "../src/index.js";

test("auth methods are stable", () => assert.equal(AuthMethod.KERBEROS, "kerberos"));
test("raw biometric material is rejected", () => {
  assert.equal(isSafePlatformBiometricProof({verifiedByPlatformAuthenticator: true, userVerification: "required", rawBiometricMaterialPresent: false}), true);
  assert.equal(isSafePlatformBiometricProof({verifiedByPlatformAuthenticator: true, userVerification: "required", rawBiometricMaterialPresent: true}), false);
});
test("global revocation requires phishing-resistant AAL2 WebAuthn", () => {
  assert.equal(RevocationScope.INTERACTIVE_SESSIONS, "interactive_sessions");
  assert.equal(isSufficientRevocationStepUp({assurance: "aal2", phishingResistant: true, authMethods: ["webauthn"]}), true);
  assert.equal(isSufficientRevocationStepUp({assurance: "aal1", phishingResistant: true, authMethods: ["webauthn"]}), false);
});
test("partial is an honest terminal job state", () => {
  assert.equal(isTerminalRevocationJobState(RevocationJobState.PARTIAL), true);
  assert.equal(isTerminalRevocationJobState(RevocationJobState.RUNNING), false);
  assert.equal(InventoryStatus.UNAVAILABLE, "unavailable");
});
test("directory admin grants use exact non-wildcard values", () => {
  assert.equal(DirectoryAdminRole.DIRECTORY_ADMIN, "directory_admin");
  assert.equal(DirectoryAdminScope.REVOCATIONS_EXECUTE, "directory.revocations.execute");
  assert.equal(Object.values(DirectoryAdminScope).some((value) => value.includes("*")), false);
});
