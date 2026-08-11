package oresinterfaces
import "testing"
func TestBiometricProofRejectsRawMaterial(t *testing.T) {
    if !(PlatformBiometricProof{VerifiedByPlatformAuthenticator:true, UserVerification:"required"}).Safe() { t.Fatal("safe platform proof rejected") }
    if (PlatformBiometricProof{VerifiedByPlatformAuthenticator:true, UserVerification:"required", RawBiometricMaterialPresent:true}).Safe() { t.Fatal("raw material accepted") }
}
func TestFactorRejectsForbiddenMaterialFlags(t *testing.T) {
	factor := Factor{Method: AuthMethodPlatformBiometric}
	if !factor.Safe() { t.Fatal("safe factor rejected") }
	factor.PrivateKeyMaterialPresent = true
	if factor.Safe() { t.Fatal("private key material flag accepted") }
}
