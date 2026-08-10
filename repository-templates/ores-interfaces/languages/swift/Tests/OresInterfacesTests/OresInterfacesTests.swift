import XCTest
@testable import OresInterfaces

final class OresInterfacesTests: XCTestCase {
    func testPlatformBiometricProofFailsClosedOnRawMaterial() {
        XCTAssertTrue(PlatformBiometricProof(
            verifiedByPlatformAuthenticator: true,
            userVerification: "required",
            rawBiometricMaterialPresent: false
        ).safe)
        XCTAssertFalse(PlatformBiometricProof(
            verifiedByPlatformAuthenticator: true,
            userVerification: "required",
            rawBiometricMaterialPresent: true
        ).safe)
    }
}
