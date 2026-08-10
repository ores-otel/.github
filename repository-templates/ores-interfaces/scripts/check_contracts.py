#!/usr/bin/env python3
from __future__ import annotations
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/ores-platform/v1/schema.json"
LANGUAGES = {"rust", "typescript", "go", "python", "dart", "java", "swift"}
AUTH_METHODS = {"jwt", "oidc", "webauthn", "totp", "kerberos", "ssh", "openpgp", "platform_biometric", "recovery"}
FORBIDDEN = re.compile(r"(?i)(BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|rawBiometric(?:Template|Image)|faceTemplate|fingerprintTemplate)")

def main() -> int:
    document = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert document["$schema"].endswith("2020-12/schema")
    methods = set(document["$defs"]["AuthMethod"]["enum"])
    assert methods == AUTH_METHODS, (methods, AUTH_METHODS)
    proof = document["$defs"]["PlatformBiometricProof"]["properties"]
    assert proof["rawBiometricMaterialPresent"]["const"] is False
    present = {path.name for path in (ROOT / "languages").iterdir() if path.is_dir()}
    assert LANGUAGES <= present, LANGUAGES - present
    for path in ROOT.rglob("*"):
        if path.resolve() == pathlib.Path(__file__).resolve():
            continue
        if path.is_file() and path.stat().st_size < 2_000_000:
            text = path.read_text(encoding="utf-8", errors="ignore")
            match = FORBIDDEN.search(text)
            if match:
                raise AssertionError(f"forbidden secret/biometric material marker in {path}: {match.group(0)}")
    print(f"contracts valid: methods={len(methods)} languages={len(present)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
