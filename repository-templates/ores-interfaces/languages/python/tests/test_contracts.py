import unittest
from ores_interfaces import PlatformBiometricProof
class ContractTests(unittest.TestCase):
    def test_biometric_proof_is_non_retaining(self):
        self.assertTrue(PlatformBiometricProof(True, "required", False).safe())
        self.assertFalse(PlatformBiometricProof(True, "required", True).safe())
if __name__ == "__main__": unittest.main()
