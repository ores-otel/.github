package oresinterfaces

import "testing"

func TestBiometricProofRejectsRawMaterial(t *testing.T) {
	if !(PlatformBiometricProof{VerifiedByPlatformAuthenticator: true, UserVerification: "required"}).Safe() {
		t.Fatal("safe platform proof rejected")
	}
	if (PlatformBiometricProof{VerifiedByPlatformAuthenticator: true, UserVerification: "required", RawBiometricMaterialPresent: true}).Safe() {
		t.Fatal("raw material accepted")
	}
}
func TestFactorRejectsForbiddenMaterialFlags(t *testing.T) {
	factor := Factor{Method: AuthMethodPlatformBiometric}
	if !factor.Safe() {
		t.Fatal("safe factor rejected")
	}
	factor.PrivateKeyMaterialPresent = true
	if factor.Safe() {
		t.Fatal("private key material flag accepted")
	}
}
func TestGlobalRevocationRequiresPhishingResistantAAL2WebAuthn(t *testing.T) {
	stepUp := RevocationStepUp{Assurance: Aal2, AuthMethods: []AuthMethod{AuthMethodWebAuthn}, PhishingResistant: true}
	if !stepUp.Sufficient() {
		t.Fatal("valid revocation step-up rejected")
	}
	stepUp.Assurance = Aal1
	if stepUp.Sufficient() {
		t.Fatal("AAL1 revocation step-up accepted")
	}
}
func TestPartialRevocationIsTerminal(t *testing.T) {
	if !RevocationPartial.Terminal() || RevocationRunning.Terminal() {
		t.Fatal("revocation terminal-state drift")
	}
	if RevocationInteractiveSessions != "interactive_sessions" {
		t.Fatal("revocation scope drift")
	}
}
func TestDirectoryAdminGrantValuesAreExact(t *testing.T) {
	if DirectoryAdmin != "directory_admin" {
		t.Fatal("directory admin role drift")
	}
	if DirectoryRevocationsExecute != "directory.revocations.execute" {
		t.Fatal("directory admin scope drift")
	}
}
