#!/usr/bin/env python3
"""Fail-closed validation for repository templates in the ores-otel fleet."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

REQUIRED_LANGUAGES = ("rust", "typescript", "go", "python", "dart", "java", "swift")
ZPKG_TARGET_KEYS = {"go": "golang"}
FORBIDDEN_PARTS = {
    ".build",
    ".dart_tool",
    ".gradle",
    ".idea",
    ".pytest_cache",
    ".terraform",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
}
FORBIDDEN_FILENAMES = {
    ".env",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
}
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("Linear token", re.compile(r"\blin_api_[A-Za-z0-9]{20,}\b")),
    ("Cloudflare token", re.compile(r"\bcfat_[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("OpenAI-style key", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b")),
)
REQUIRED_ROOT_FILES = (
    ".github/workflows/ci.yml",
    ".gitignore",
    ".zpkg.toml",
    "LICENSE",
    "README.md",
)


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid JSON {path}: {error}") from error


def load_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValidationError(f"invalid TOML {path}: {error}") from error


def iter_template_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ValidationError(f"template symlink is not permitted: {relative}")
        if not path.is_file():
            continue
        if any(part in FORBIDDEN_PARTS for part in relative.parts):
            raise ValidationError(f"generated/build path is not permitted: {relative}")
        if path.name in FORBIDDEN_FILENAMES or path.name.startswith(".env."):
            raise ValidationError(f"plaintext environment or private-key file is not permitted: {relative}")
        if path.suffix in {".class", ".o", ".pyc", ".so", ".dylib", ".dll", ".exe"}:
            raise ValidationError(f"compiled artifact is not permitted: {relative}")
        files.append(path)
    if not files:
        raise ValidationError(f"template contains no files: {root}")
    return files


def scan_text(path: Path, relative: Path) -> str:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise ValidationError(f"template files must be UTF-8 text: {relative}: {error}") from error
    if "\x00" in text:
        raise ValidationError(f"NUL byte is not permitted: {relative}")
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise ValidationError(f"possible {label} in template: {relative}")
    return text


def validate_zpkg(root: Path, spec: dict[str, Any]) -> None:
    manifest = load_toml(root / ".zpkg.toml")
    package = manifest.get("package", {})
    if package.get("org") != spec["organization"]:
        raise ValidationError(f"{spec['name']}: .zpkg.toml package.org does not match fleet")
    if package.get("name") != spec["name"]:
        raise ValidationError(f"{spec['name']}: .zpkg.toml package.name does not match fleet")
    if package.get("version") != "0.1.0":
        raise ValidationError(f"{spec['name']}: initial package version must be 0.1.0")
    repository = package.get("repository", {})
    expected_url = f"https://github.com/{spec['organization']}/{spec['name']}"
    if repository.get("url") != expected_url:
        raise ValidationError(f"{spec['name']}: repository URL must be {expected_url}")
    targets = manifest.get("targets", {})
    missing_targets = [
        language for language in REQUIRED_LANGUAGES
        if ZPKG_TARGET_KEYS.get(language, language) not in targets
    ]
    if missing_targets:
        raise ValidationError(f"{spec['name']}: missing Zed targets: {', '.join(missing_targets)}")
    for language in REQUIRED_LANGUAGES:
        target_key = ZPKG_TARGET_KEYS.get(language, language)
        target_dir = targets[target_key].get("dir")
        if target_dir != f"langs/{language}":
            raise ValidationError(
                f"{spec['name']}: target {language!r} must use langs/{language}, got {target_dir!r}"
            )
        if not (root / target_dir).is_dir():
            raise ValidationError(f"{spec['name']}: target directory missing: {target_dir}")

    publish = manifest.get("publish", {})
    smoke_test = publish.get("smoke_test")
    if not isinstance(smoke_test, str) or not smoke_test.startswith("python3 scripts/"):
        raise ValidationError(f"{spec['name']}: publish.smoke_test must use the checked-in validator")


def validate_interfaces(root: Path) -> None:
    schema_path = root / "contracts/ores-platform/v1/schema.json"
    schema = load_json(schema_path)
    methods = schema.get("$defs", {}).get("AuthMethod", {}).get("enum", [])
    required_methods = {
        "jwt",
        "oidc",
        "webauthn",
        "totp",
        "kerberos",
        "ssh",
        "openpgp",
        "platform_biometric",
        "recovery",
    }
    if set(methods) != required_methods:
        raise ValidationError(
            "ores-interfaces: AuthMethod must exactly cover the reviewed methods; "
            f"got {sorted(methods)}"
        )
    definitions = schema.get("$defs", {})
    biometric = definitions.get("PlatformBiometricProof", {})
    required = set(biometric.get("required", []))
    if not {
        "verifiedByPlatformAuthenticator",
        "userVerification",
        "rawBiometricMaterialPresent",
    }.issubset(required):
        raise ValidationError("ores-interfaces: biometric proof must carry non-retention invariants")
    retained = (
        biometric.get("properties", {})
        .get("rawBiometricMaterialPresent", {})
        .get("const")
    )
    if retained is not False:
        raise ValidationError("ores-interfaces: raw biometric material must be forbidden by contract")


def validate_core(root: Path) -> None:
    manifest = load_toml(root / ".zpkg.toml")
    dependencies = manifest.get("dependencies", {})
    required = {
        "ores-otel/ores-interfaces": "^0.1.0",
        "oresoftware/next-loggers": "^0.1.0",
    }
    if dependencies != required:
        raise ValidationError(
            f"ores-lib-core: Zed dependencies must be exactly {required!r}, got {dependencies!r}"
        )
    policy = load_json(root / "contracts/dependencies.json")
    entries = {entry.get("package"): entry for entry in policy.get("dependencies", [])}
    logger = entries.get("oresoftware/next-loggers", {})
    if logger.get("repository") != "ores-otel/ores.otel.log":
        raise ValidationError("ores-lib-core: logger dependency policy must name ores.otel.log")
    if "ores-otel/ores-interfaces" not in entries:
        raise ValidationError("ores-lib-core: interface dependency policy mismatch")
    if policy.get("globalProviderInstallationAllowed") is not False:
        raise ValidationError("ores-lib-core: application must retain global telemetry-provider ownership")
    if policy.get("rawBiometricMaterialAllowed") is not False:
        raise ValidationError("ores-lib-core: raw biometric material must remain forbidden")


def validate_template(manifest_root: Path, spec: dict[str, Any]) -> tuple[int, int]:
    template = spec.get("template")
    if not isinstance(template, str) or not template:
        raise ValidationError(f"{spec.get('name', '<unnamed>')}: template path missing")
    root = (manifest_root / template).resolve()
    expected_parent = (manifest_root / "repository-templates").resolve()
    if root.parent != expected_parent:
        raise ValidationError(f"{spec['name']}: template must be a direct child of repository-templates")
    if not root.is_dir():
        raise ValidationError(f"{spec['name']}: template directory missing: {root}")
    for required in REQUIRED_ROOT_FILES:
        if not (root / required).is_file():
            raise ValidationError(f"{spec['name']}: missing required template file: {required}")
    for language in REQUIRED_LANGUAGES:
        if not (root / "langs" / language).is_dir():
            raise ValidationError(f"{spec['name']}: missing language directory: langs/{language}")

    files = iter_template_files(root)
    line_count = 0
    for path in files:
        text = scan_text(path, path.relative_to(root))
        line_count += text.count("\n") + bool(text)
        if path.suffix == ".json":
            load_json(path)
        elif path.suffix == ".toml" or path.name == "Cargo.toml" or path.name == "pyproject.toml":
            load_toml(path)

    validate_zpkg(root, spec)
    if spec["name"] == "ores-interfaces":
        validate_interfaces(root)
    elif spec["name"] == "ores-lib-core":
        validate_core(root)
    else:
        raise ValidationError(f"unreviewed shared repository template: {spec['name']}")
    return len(files), line_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("repository-fleet.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    manifest = load_json(manifest_path)
    if manifest.get("fleetVersion") != "ores.otel.repository-fleet/v2":
        raise ValidationError("unsupported or stale repository fleet version")
    shared = manifest.get("sharedRepositories")
    if not isinstance(shared, list) or len(shared) != 2:
        raise ValidationError("fleet must declare exactly the two reviewed shared repositories")
    names = [entry.get("name") for entry in shared]
    if names != ["ores-interfaces", "ores-lib-core"]:
        raise ValidationError(f"shared repository order/scope drift: {names!r}")

    total_files = 0
    total_lines = 0
    for spec in shared:
        files, lines = validate_template(manifest_path.parent, spec)
        total_files += files
        total_lines += lines
        print(f"validated {spec['organization']}/{spec['name']}: files={files} lines={lines}")
    print(
        "repository templates valid: "
        f"repositories={len(shared)} languages={len(REQUIRED_LANGUAGES)} files={total_files} lines={total_lines}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as error:
        print(f"validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
