import unittest
from ores_interfaces import (
    AssuranceLevel,
    AuthMethod,
    DirectoryAdminGrant,
    DirectoryAdminRole,
    DirectoryAdminScope,
    PlatformBiometricProof,
    RevocationJobState,
    RevocationScope,
    RevocationStepUp,
)
class ContractTests(unittest.TestCase):
    def test_biometric_proof_is_non_retaining(self):
        self.assertTrue(PlatformBiometricProof(True, "required", False).safe())
        self.assertFalse(PlatformBiometricProof(True, "required", True).safe())
    def test_global_revocation_requires_phishing_resistant_aal2_webauthn(self):
        self.assertEqual(RevocationScope.INTERACTIVE_SESSIONS, "interactive_sessions")
        valid = RevocationStepUp(
            "principal-operator",
            "actor_session_hash_01",
            "step_up_evidence_hash_01",
            AssuranceLevel.AAL2,
            (AuthMethod.WEBAUTHN,),
            True,
            "2026-08-11T15:00:00Z",
            "2026-08-11T15:05:00Z",
        )
        self.assertTrue(valid.sufficient())
        self.assertFalse(RevocationStepUp(
            valid.actor_principal_id,
            valid.actor_session_id_hash,
            valid.evidence_id_hash,
            AssuranceLevel.AAL1,
            valid.auth_methods,
            valid.phishing_resistant,
            valid.verified_at,
            valid.fresh_until,
        ).sufficient())
    def test_partial_revocation_is_terminal(self):
        self.assertTrue(RevocationJobState.PARTIAL.terminal())
        self.assertFalse(RevocationJobState.RUNNING.terminal())
    def test_directory_admin_grant_is_explicit(self):
        grant = DirectoryAdminGrant(
            "20000000-0000-4000-8000-000000000001",
            "10000000-0000-4000-8000-000000000001",
            None,
            (DirectoryAdminScope.DASHBOARD_READ,),
            (DirectoryAdminRole.DIRECTORY_ADMIN,),
            "2026-08-11T21:00:00Z",
            None,
        )
        self.assertTrue(grant.is_directory_admin())
        self.assertNotIn("*", grant.scopes[0])
if __name__ == "__main__": unittest.main()
