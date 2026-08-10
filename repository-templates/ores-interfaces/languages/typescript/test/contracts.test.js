import test from "node:test";
import assert from "node:assert/strict";
import {AuthMethod, isSafePlatformBiometricProof} from "../src/index.js";

test("auth methods are stable", () => assert.equal(AuthMethod.KERBEROS, "kerberos"));
test("raw biometric material is rejected", () => {
  assert.equal(isSafePlatformBiometricProof({verifiedByPlatformAuthenticator: true, userVerification: "required", rawBiometricMaterialPresent: false}), true);
  assert.equal(isSafePlatformBiometricProof({verifiedByPlatformAuthenticator: true, userVerification: "required", rawBiometricMaterialPresent: true}), false);
});
