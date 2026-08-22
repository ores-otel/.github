package oresinterfaces
import "testing"
func TestBiometricProofRejectsRawMaterial(t *testing.T) {
    if !(PlatformBiometricProof{VerifiedByPlatformAuthenticator:true, UserVerification:"required"}).Safe() { t.Fatal("safe platform proof rejected") }
    if (PlatformBiometricProof{VerifiedByPlatformAuthenticator:true, UserVerification:"required", RawBiometricMaterialPresent:true}).Safe() { t.Fatal("raw material accepted") }
}
