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

    func testGlobalRevocationRequiresPhishingResistantAAL2WebAuthn() {
        let stepUp = RevocationStepUp(
            actorPrincipalId: "principal-operator",
            actorSessionIdHash: "actor_session_hash_01",
            evidenceIdHash: "step_up_evidence_hash_01",
            assurance: .aal2,
            authMethods: [.webauthn],
            phishingResistant: true,
            verifiedAt: "2026-08-11T15:00:00Z",
            freshUntil: "2026-08-11T15:05:00Z"
        )
        XCTAssertTrue(stepUp.sufficient)
        XCTAssertEqual(RevocationScope.interactiveSessions.rawValue, "interactive_sessions")
    }

    func testPartialRevocationIsTerminal() {
        XCTAssertTrue(RevocationJobState.partial.terminal)
        XCTAssertFalse(RevocationJobState.running.terminal)
    }

    func testDirectoryAdminValuesAreExact() {
        XCTAssertEqual(DirectoryAdminRole.directoryAdmin.rawValue, "directory_admin")
        XCTAssertEqual(
            DirectoryAdminScope.revocationsExecute.rawValue,
            "directory.revocations.execute"
        )
    }
}
