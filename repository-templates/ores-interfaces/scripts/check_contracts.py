#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from importlib.metadata import PackageNotFoundError, version
import json
import pathlib
import re
from copy import deepcopy
from datetime import datetime
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import best_match
except ModuleNotFoundError as error:
    raise SystemExit(
        "missing pinned contract validator dependency; install it with "
        "`python3 -m pip install --require-hashes "
        "--requirement scripts/requirements-contracts.lock`"
    ) from error

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR_LOCK = ROOT / "scripts/requirements-contracts.lock"
PLATFORM_SCHEMA = ROOT / "contracts/ores-platform/v1/schema.json"
ADMIN_SCHEMA = ROOT / "contracts/shared-auth-admin/v1/schema.json"
ADMIN_EXAMPLE = ROOT / "contracts/shared-auth-admin/v1/examples/dashboard-response.json"
ADMIN_EXAMPLES = ROOT / "contracts/shared-auth-admin/v1/examples"
ADMIN_VALID_FIXTURES = ROOT / "contracts/shared-auth-admin/v1/fixtures/valid"
ADMIN_INVALID_FIXTURES = ROOT / "contracts/shared-auth-admin/v1/fixtures/invalid"
SHARED_AUTH_SCHEMA = ROOT / "contracts/shared-auth/v1/schema.json"
REVOCATION_REQUEST_EXAMPLE = (
    ROOT / "contracts/shared-auth/v1/examples/revoke-sessions-request.json"
)
REVOCATION_RESULT_EXAMPLE = (
    ROOT / "contracts/shared-auth/v1/examples/revoke-sessions-result.json"
)
LANGUAGES = {"rust", "typescript", "go", "python", "dart", "java", "swift"}
AUTH_METHODS = {
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
REVOCATION_CONTRACTS = {
    "PrincipalSearchRequest",
    "PrincipalSearchResult",
    "PrincipalSelectionRequest",
    "PrincipalSelectionResult",
    "GlobalRevocationPreviewRequest",
    "GlobalRevocationCommitAuthorization",
    "AdminRevocationTokenExchangeRequest",
    "AdminRevocationTokenExchangeResult",
    "GlobalRevocationPreview",
    "GlobalRevocationRequest",
    "GlobalRevocationOperation",
}
ADMIN_CONTRACTS = (
    "DashboardQuery",
    "DashboardResponse",
    "OrganizationOption",
    "ProjectOption",
    "UserProjection",
    "SessionProjection",
    "RoleBindingProjection",
    "CredentialCapabilityProjection",
    "PrincipalSearchRequest",
    "PrincipalSearchResult",
    "PrincipalSelectionRequest",
    "PrincipalSelectionResult",
    "GlobalRevocationPreviewRequest",
    "GlobalRevocationCommitAuthorization",
    "AdminRevocationTokenExchangeRequest",
    "AdminRevocationTokenExchangeResult",
    "GlobalRevocationPreview",
    "GlobalRevocationRequest",
    "GlobalRevocationOperation",
    "DirectoryAdminGrant",
    "DirectoryAdminGrantSet",
)
DIRECTORY_ADMIN_SCOPES = {
    "directory.dashboard.read",
    "directory.users.read",
    "directory.sessions.read",
    "directory.roles.read",
    "directory.revocations.read",
    "directory.revocations.execute",
}
DIRECTORY_ADMIN_ROLES = {
    "directory_admin",
    "directory_security_operator",
    "directory_auditor",
}
DIRECTORY_ADMIN_TYPES = {
    "DirectoryAdminScope",
    "DirectoryAdminRole",
    "DirectoryAdminGrant",
    "DirectoryAdminGrantSet",
}
DIRECTORY_ADMIN_FIELDS = {
    "grantId",
    "organizationId",
    "projectIds",
    "scopes",
    "roles",
    "grantedAt",
    "expiresAt",
    "principalId",
    "audience",
    "assurance",
    "directoryGrants",
    "evaluatedAt",
    "exactOrganizationMatchRequired",
    "crossOrganizationFallbackAllowed",
    "rawEmailsPresent",
}
PINNED_VALIDATOR_PACKAGES = {
    "jsonschema": "4.25.1",
    "rfc3339-validator": "0.1.4",
}
REVOCATION_SCOPES = {
    "interactive_sessions",
    "refresh_token_families",
    "offline_grants",
    "downstream_sessions",
    "impersonation_sessions",
    "user_api_credentials",
    "registered_device_sessions",
}
REVOCATION_JOB_STATES = {"queued", "running", "partial", "succeeded", "failed", "cancelled"}
REVOCATION_TARGET_STATES = {
    "pending",
    "running",
    "retry_scheduled",
    "succeeded",
    "failed",
    "skipped",
    "unsupported",
}
REVOCATION_TYPES = {
    "PrincipalSearchState",
    "RevocationScope",
    "RevocationJobState",
    "RevocationTargetState",
    "RevocationRedaction",
    "ProviderIdentityRef",
    "PrincipalSearchRequest",
    "PrincipalSearchCandidate",
    "PrincipalSearchResult",
    "PrincipalSelectionRequest",
    "PrincipalSelectionResult",
    "GlobalRevocationPreviewRequest",
    "GlobalRevocationCommitAuthorization",
    "AdminTokenExchangeRedaction",
    "AdminRevocationTokenExchangeRequest",
    "AdminRevocationTokenExchangeResult",
    "InventoryStatus",
    "RevocationBlastRadius",
    "RevocationPreviewTarget",
    "GlobalRevocationPreview",
    "RevocationStepUp",
    "RevocationRequestCorrelation",
    "GlobalRevocationRequest",
    "RevocationTargetResult",
    "RevocationFence",
    "RevocationAuditCorrelation",
    "GlobalRevocationOperation",
}
REVOCATION_FIELDS = {
    "providerTenantId",
    "opaqueIdentityHandle",
    "principalId",
    "emailSearchKeyHash",
    "lookupId",
    "selectionId",
    "selectionConfirmed",
    "commitAuthorizationId",
    "verifiedStepUp",
    "dualControlRequired",
    "dualControlSatisfied",
    "previewCreatedByPrincipalIdHash",
    "commitAuthorizedByPrincipalIdHash",
    "commitAuthorizedBySessionIdHash",
    "subjectToken",
    "subjectTokenType",
    "requestedScope",
    "accessToken",
    "issuedTokenType",
    "tokenType",
    "expiresInSeconds",
    "authorizedParty",
    "tokensReturnedInDiagnostics",
    "requiresExplicitPrincipalSelection",
    "selectedScopes",
    "blastRadius",
    "inventoryStatus",
    "unknownFields",
    "idempotencyKey",
    "phishingResistant",
    "freshUntil",
    "attemptCount",
    "retryable",
    "nextAttemptAt",
    "resultCode",
    "residualAccessTokenMaxSeconds",
    "appliedAt",
    "notBefore",
    "previousAuthEpoch",
    "authEpoch",
    "idempotencyKeyHash",
    "actorSessionIdHash",
    "rawEmailsPresent",
    "rawTokensPresent",
    "rawBiometricMaterialPresent",
}
INVENTORY_COUNT_FIELDS = {
    "providerTenantCount",
    "identityCount",
    "organizationCount",
    "projectCount",
    "interactiveSessionCount",
    "refreshTokenFamilyCount",
    "offlineGrantCount",
    "downstreamSessionCount",
    "impersonationSessionCount",
    "userApiCredentialCount",
    "registeredDeviceSessionCount",
}
LANGUAGE_BINDINGS = {
    "rust": ROOT / "langs/rust/src/lib.rs",
    "typescript": ROOT / "langs/typescript/src/index.d.ts",
    "go": ROOT / "langs/go/interfaces.go",
    "python": ROOT / "langs/python/src/ores_interfaces/__init__.py",
    "dart": ROOT / "langs/dart/lib/ores_interfaces.dart",
    "java": ROOT / "langs/java/src/main/java/com/oresoftware/interfaces/AuthContracts.java",
    "swift": ROOT / "langs/swift/Sources/OresInterfaces/OresInterfaces.swift",
}
REVOCATION_EXAMPLE_NAMES = {
    "principal-search-request.json",
    "principal-search-result.json",
    "global-revocation-preview.json",
    "global-revocation-request.json",
    "global-revocation-operation.json",
    "global-revocation-operation-running.json",
}
EXAMPLE_DEFINITIONS = {
    "dashboard-response.json": "DashboardResponse",
    "principal-search-request.json": "PrincipalSearchRequest",
    "principal-search-result.json": "PrincipalSearchResult",
    "global-revocation-preview.json": "GlobalRevocationPreview",
    "global-revocation-request.json": "GlobalRevocationRequest",
    "global-revocation-operation.json": "GlobalRevocationOperation",
    "global-revocation-operation-running.json": "GlobalRevocationOperation",
}
EMAIL_VALUE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SKIP_PARTS = {".git", "target", "node_modules", "__pycache__", ".dart_tool", "build", ".vendor", "zed_modules"}
SKIP_SUFFIXES = {".pyc", ".class", ".o", ".a", ".so", ".dylib", ".dll", ".exe", ".jar"}
FORBIDDEN = re.compile(
    r"(?i)(BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|rawBiometric(?:Template|Image)|faceTemplate|fingerprintTemplate)"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError(f"cannot load JSON fixture {path.relative_to(ROOT)}: {error}") from error


def format_validation_error(error: Any) -> str:
    path = "$"
    for component in error.absolute_path:
        if isinstance(component, int):
            path += f"[{component}]"
        else:
            path += f".{component}"
    return f"{path}: {error.message}"


def require_valid(
    validator: Draft202012Validator,
    document: Any,
    label: pathlib.Path | str,
) -> None:
    errors = list(validator.iter_errors(document))
    if errors:
        error = best_match(errors)
        raise AssertionError(
            f"expected valid admin fixture {label}; {format_validation_error(error)}"
        )


def require_invalid(
    validator: Draft202012Validator,
    document: Any,
    label: pathlib.Path | str,
) -> None:
    if validator.is_valid(document):
        raise AssertionError(f"expected invalid admin fixture {label}, but it validated")


def require_restrictive_objects(node: Any, path: str = "$") -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            require(
                node.get("additionalProperties") is False,
                f"object schema at {path} must set additionalProperties to false",
            )
        for key, value in node.items():
            require_restrictive_objects(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            require_restrictive_objects(value, f"{path}[{index}]")


def validate_discriminator(schema: dict[str, Any]) -> None:
    expected = {contract: f"#/$defs/{contract}" for contract in ADMIN_CONTRACTS}
    actual: dict[str, str] = {}
    for index, branch in enumerate(schema.get("oneOf", [])):
        properties = branch.get("properties", {})
        contract = properties.get("contract", {}).get("const")
        payload_ref = properties.get("payload", {}).get("$ref")
        require(
            isinstance(contract, str) and isinstance(payload_ref, str),
            f"admin oneOf branch {index} must bind a contract const to a payload $ref",
        )
        require(contract not in actual, f"duplicate admin discriminator branch: {contract}")
        actual[contract] = payload_ref
    require(
        actual == expected,
        f"admin discriminator mapping drifted: actual={actual!r} expected={expected!r}",
    )


def validate_validator_dependencies() -> None:
    require(VALIDATOR_LOCK.is_file(), "pinned contract validator lock is missing")
    for package, expected in PINNED_VALIDATOR_PACKAGES.items():
        try:
            installed = version(package)
        except PackageNotFoundError as error:
            raise AssertionError(f"required validator package is missing: {package}") from error
        require(
            installed == expected,
            f"validator dependency drift: {package}={installed}, expected {expected}",
        )


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_revocation_redaction(value: dict[str, object]) -> None:
    assert value == {
        "rawEmailsPresent": False,
        "rawTokensPresent": False,
        "rawSessionIdentifiersPresent": False,
        "rawBiometricMaterialPresent": False,
    }


def validate_schema_value(
    value: object,
    schema: dict[str, object] | bool,
    root: dict[str, object],
    path: str = "$",
) -> None:
    if schema is False:
        raise AssertionError(f"prohibited value at {path}")
    if schema is True:
        return

    reference = schema.get("$ref")
    if reference is not None:
        require(
            isinstance(reference, str) and reference.startswith("#/$defs/"),
            f"unsupported ref at {path}: {reference}",
        )
        definition = reference.removeprefix("#/$defs/")
        validate_schema_value(value, root["$defs"][definition], root, path)

    if "const" in schema:
        require(value == schema["const"], f"const mismatch at {path}: {value!r}")
    if "enum" in schema:
        require(value in schema["enum"], f"enum mismatch at {path}: {value!r}")

    expected_types = schema.get("type")
    if isinstance(expected_types, str):
        expected_types = [expected_types]
    if expected_types is not None:
        type_matches = {
            "object": lambda candidate: isinstance(candidate, dict),
            "array": lambda candidate: isinstance(candidate, list),
            "string": lambda candidate: isinstance(candidate, str),
            "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
            "boolean": lambda candidate: isinstance(candidate, bool),
            "null": lambda candidate: candidate is None,
        }
        require(
            any(type_matches[item](value) for item in expected_types),
            f"type mismatch at {path}: {value!r}",
        )

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        require(
            required <= set(value),
            f"missing fields at {path}: {sorted(required - set(value))}",
        )
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            require(
                set(value) <= set(properties),
                f"additional fields at {path}: {sorted(set(value) - set(properties))}",
            )
        for key, child in value.items():
            if key in properties:
                validate_schema_value(child, properties[key], root, f"{path}.{key}")

    if isinstance(value, list):
        if "minItems" in schema:
            require(len(value) >= schema["minItems"], f"too few items at {path}")
        if "maxItems" in schema:
            require(len(value) <= schema["maxItems"], f"too many items at {path}")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            require(len(canonical) == len(set(canonical)), f"duplicate items at {path}")
        if "items" in schema:
            for index, child in enumerate(value):
                validate_schema_value(child, schema["items"], root, f"{path}[{index}]")
        if "contains" in schema:
            require(
                any(schema_matches(item, schema["contains"], root) for item in value),
                f"contains failed at {path}",
            )

    if isinstance(value, str):
        if "minLength" in schema:
            require(len(value) >= schema["minLength"], f"string too short at {path}")
        if "maxLength" in schema:
            require(len(value) <= schema["maxLength"], f"string too long at {path}")
        if "pattern" in schema:
            require(
                re.search(schema["pattern"], value) is not None,
                f"pattern mismatch at {path}: {value!r}",
            )
        if schema.get("format") == "date-time":
            timestamp(value)

    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema:
            require(value >= schema["minimum"], f"minimum failed at {path}")
        if "maximum" in schema:
            require(value <= schema["maximum"], f"maximum failed at {path}")

    for constraint in schema.get("allOf", []):
        validate_schema_value(value, constraint, root, path)
    if "if" in schema and schema_matches(value, schema["if"], root):
        validate_schema_value(value, schema.get("then", {}), root, path)


def schema_matches(value: object, schema: dict[str, object] | bool, root: dict[str, object]) -> bool:
    try:
        validate_schema_value(value, schema, root)
    except AssertionError:
        return False
    return True


def validate_admin_contract() -> None:
    validate_validator_dependencies()
    schema = load_json(ADMIN_SCHEMA)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)
    require_restrictive_objects(schema)
    validate_discriminator(schema)

    format_checker = FormatChecker()
    assert format_checker.conforms("2026-08-11T21:30:00Z", "date-time")
    assert not format_checker.conforms("not-a-date-time", "date-time")
    assert format_checker.conforms("10000000-0000-4000-8000-000000000001", "uuid")
    assert not format_checker.conforms("not-a-uuid", "uuid")
    validator = Draft202012Validator(schema, format_checker=format_checker)

    definitions = schema["$defs"]
    capabilities = definitions["CredentialCapabilityProjection"]
    dashboard = definitions["DashboardResponse"]

    assert set(schema["properties"]["contract"]["enum"]) == set(ADMIN_CONTRACTS)
    assert set(definitions["RevocationScope"]["enum"]) == REVOCATION_SCOPES
    assert set(definitions["RevocationJobState"]["enum"]) == REVOCATION_JOB_STATES
    assert set(definitions["RevocationTargetState"]["enum"]) == REVOCATION_TARGET_STATES

    provider_identity = definitions["ProviderIdentityRef"]
    assert set(provider_identity["required"]) == {
        "providerId",
        "providerTenantId",
        "opaqueIdentityHandle",
    }
    assert "email" not in provider_identity["properties"]
    assert "token" not in provider_identity["properties"]

    search_request = definitions["PrincipalSearchRequest"]
    assert "emailSearchKeyHash" in search_request["properties"]
    assert "email" not in search_request["properties"]
    assert search_request["properties"]["purpose"]["const"] == "operator_email_search"
    assert definitions["IdempotencyKey"]["writeOnly"] is True

    search_candidate = definitions["PrincipalSearchCandidate"]
    assert "principalId" in search_candidate["required"]
    assert "principalId" in search_candidate["properties"]

    selection_request = definitions["PrincipalSelectionRequest"]
    assert selection_request["properties"]["selectionConfirmed"]["const"] is True
    assert {"lookupId", "principalId"} <= set(selection_request["required"])
    assert not ({"email", "emailSearchKeyHash"} & set(selection_request["properties"]))

    selection_result = definitions["PrincipalSelectionResult"]
    assert selection_result["properties"]["selectionId"]["$ref"] == (
        "#/$defs/OpaqueSelectionId"
    )
    assert {"selectionId", "lookupId", "principalId", "selectedAt", "expiresAt"} <= set(
        selection_result["required"]
    )

    preview_request = definitions["GlobalRevocationPreviewRequest"]
    assert preview_request["properties"]["selectionId"]["$ref"] == (
        "#/$defs/OpaqueSelectionId"
    )
    assert not ({"principalId", "email", "emailSearchKeyHash"} & set(
        preview_request["properties"]
    ))

    scopes = definitions["RevocationScopeSet"]
    mandatory_scopes = {item["contains"]["const"] for item in scopes["allOf"]}
    assert mandatory_scopes == {"interactive_sessions", "refresh_token_families"}

    preview = definitions["GlobalRevocationPreview"]
    assert preview["properties"]["ambiguityResolved"]["const"] is True
    assert preview["properties"]["requiresStepUp"]["const"] is True
    assert preview["properties"]["minimumAssurance"]["const"] == "aal2"
    assert preview["properties"]["phishingResistantStepUpRequired"]["const"] is True
    blast_radius = definitions["RevocationBlastRadius"]
    assert set(blast_radius["properties"]) == INVENTORY_COUNT_FIELDS | {
        "inventoryStatus",
        "unknownFields",
    }
    assert set(blast_radius["properties"]["unknownFields"]["items"]["enum"]) == (
        INVENTORY_COUNT_FIELDS
    )
    assert set(definitions["InventoryStatus"]["enum"]) == {
        "complete",
        "partial",
        "unavailable",
    }

    step_up = definitions["RevocationStepUp"]
    assert set(step_up["properties"]["assurance"]["enum"]) == {"aal2", "aal3"}
    assert step_up["properties"]["authMethods"]["contains"]["const"] == "webauthn"
    assert step_up["properties"]["phishingResistant"]["const"] is True
    assert {"verifiedAt", "freshUntil"} <= set(step_up["required"])

    request = definitions["GlobalRevocationRequest"]
    assert {
        "previewId",
        "commitAuthorizationId",
        "idempotencyKey",
        "selectedScopes",
    } <= set(request["required"])
    assert not ({"principalId", "principalSelectionConfirmed", "stepUp"} & set(
        request["properties"]
    ))

    commit_authorization = definitions["GlobalRevocationCommitAuthorization"]
    assert commit_authorization["properties"]["commitAuthorizationId"]["$ref"] == (
        "#/$defs/OpaqueCommitAuthorizationId"
    )
    assert commit_authorization["properties"]["dualControlSatisfied"]["const"] is True
    assert commit_authorization["properties"]["verifiedStepUp"]["$ref"] == (
        "#/$defs/RevocationStepUp"
    )

    exchange_request = definitions["AdminRevocationTokenExchangeRequest"]
    assert exchange_request["properties"]["subjectToken"]["writeOnly"] is True
    assert exchange_request["properties"]["audience"]["const"] == (
        "shared-auth-web-server"
    )
    assert exchange_request["properties"]["requestedScope"]["const"] == (
        "shared-auth:sessions:revoke:global"
    )
    assert not ({"azp", "authorizedParty"} & set(exchange_request["properties"]))

    exchange_result = definitions["AdminRevocationTokenExchangeResult"]
    assert exchange_result["properties"]["accessToken"]["writeOnly"] is True
    assert exchange_result["properties"]["tokenType"]["const"] == "Bearer"
    assert exchange_result["properties"]["audience"]["const"] == (
        "shared-auth-web-server"
    )
    assert exchange_result["properties"]["authorizedParty"]["const"] == (
        "shared-auth-web-server"
    )
    assert exchange_result["properties"]["scope"]["const"] == (
        "shared-auth:sessions:revoke:global"
    )
    assert exchange_result["properties"]["expiresInSeconds"]["maximum"] == 300

    operation = definitions["GlobalRevocationOperation"]
    assert {"principalId", "state", "fence", "targets", "audit"} <= set(operation["required"])
    fence = definitions["RevocationFence"]
    assert {"appliedAt", "notBefore", "previousAuthEpoch", "authEpoch", "effective"} == set(fence["required"])
    assert fence["properties"]["effective"]["const"] is True

    audit = definitions["RevocationAuditCorrelation"]
    for field in ("rawEmailsPresent", "rawTokensPresent", "rawBiometricMaterialPresent"):
        assert audit["properties"][field]["const"] is False

    directory_grant = definitions["DirectoryAdminGrant"]
    directory_grant_set = definitions["DirectoryAdminGrantSet"]
    assert set(definitions["DirectoryAdminScope"]["enum"]) == DIRECTORY_ADMIN_SCOPES
    assert set(definitions["DirectoryAdminRole"]["enum"]) == DIRECTORY_ADMIN_ROLES
    assert directory_grant["properties"]["grantId"]["$ref"] == "#/$defs/Uuid"
    assert directory_grant["properties"]["organizationId"]["$ref"] == "#/$defs/Uuid"
    project_ids = directory_grant["properties"]["projectIds"]
    assert project_ids["minItems"] == 1
    assert project_ids["uniqueItems"] is True
    assert project_ids["items"]["$ref"] == "#/$defs/Uuid"
    assert "projectIds" not in directory_grant["required"]
    assert directory_grant["properties"]["roles"]["contains"]["const"] == "directory_admin"
    assert not ({"email", "rawEmail", "normalizedEmail"} & set(directory_grant["properties"]))

    grant_set_properties = directory_grant_set["properties"]
    assert grant_set_properties["schema"]["const"] == (
        "ores.shared-auth-admin-directory-grant-set/v1"
    )
    assert grant_set_properties["assurance"]["enum"] == ["aal2", "aal3"]
    assert grant_set_properties["directoryGrants"]["items"]["$ref"] == (
        "#/$defs/DirectoryAdminGrant"
    )
    assert grant_set_properties["exactOrganizationMatchRequired"]["const"] is True
    assert grant_set_properties["crossOrganizationFallbackAllowed"]["const"] is False
    assert grant_set_properties["rawEmailsPresent"]["const"] is False
    assert "expiresAt" in directory_grant_set["required"]
    assert grant_set_properties["expiresAt"]["$ref"] == "#/$defs/IsoTimestamp"
    assert not ({"organizationId", "projectId", "projectIds", "scopes", "roles"} & set(
        grant_set_properties
    ))

    capability_required = set(capabilities["required"])
    assert {
        "productionEnabled",
        "requiresOnlineIntrospection",
        "roleClaimsAuthoritative",
        "rawBiometricMaterialPresent",
    } <= capability_required

    scope = dashboard["properties"]["scope"]["properties"]
    assert scope["exactMembershipRequired"]["const"] is True
    assert scope["crossOrganizationFallbackAllowed"]["const"] is False

    redaction = dashboard["properties"]["redaction"]["properties"]
    for field in (
        "rawSessionIdentifiersPresent",
        "bearerTokensPresent",
        "rawIpAddressesPresent",
        "rawBiometricMaterialPresent",
    ):
        assert redaction[field]["const"] is False

    dashboard_envelope = load_json(ADMIN_EXAMPLE)
    require_valid(validator, dashboard_envelope, ADMIN_EXAMPLE.relative_to(ROOT))
    assert dashboard_envelope["contract"] == "DashboardResponse"
    example = dashboard_envelope["payload"]
    assert example["schema"] == "ores.shared-auth-admin-dashboard/v1"
    assert example["scope"]["exactMembershipRequired"] is True
    assert example["scope"]["crossOrganizationFallbackAllowed"] is False
    assert all(value is False for value in example["redaction"].values())

    capabilities_by_method = {item["method"]: item for item in example["capabilities"]}
    ssh = capabilities_by_method["ssh"]
    assert ssh["productionEnabled"] is False
    assert ssh["requiresOnlineIntrospection"] is True
    assert ssh["maximumAssurance"] in {"aal0", "aal1"}
    assert ssh["roleClaimsAuthoritative"] is False

    openpgp = capabilities_by_method["openpgp"]
    assert openpgp["authority"] == "provenance_only"
    assert openpgp["tokenMintingAllowed"] is False
    assert openpgp["maximumAssurance"] == "aal0"

    biometric = capabilities_by_method["platform_biometric"]
    assert biometric["rawBiometricMaterialPresent"] is False
    assert biometric["retention"] == "none"

    example_names = {path.name for path in ADMIN_EXAMPLES.glob("*.json")}
    assert REVOCATION_EXAMPLE_NAMES <= example_names
    examples = {
        name: load_json(ADMIN_EXAMPLES / name)
        for name in EXAMPLE_DEFINITIONS
    }
    examples["dashboard-response.json"] = example
    for name, definition in EXAMPLE_DEFINITIONS.items():
        validate_schema_value(examples[name], definitions[definition], schema)
        if definition in REVOCATION_CONTRACTS:
            require_valid(
                validator,
                {"contract": definition, "payload": examples[name]},
                f"generated envelope for {name}",
            )

    canonical_documents: dict[str, tuple[pathlib.Path | str, dict[str, Any]]] = {
        "DashboardResponse": (ADMIN_EXAMPLE.relative_to(ROOT), dashboard_envelope),
    }
    valid_paths = sorted(ADMIN_VALID_FIXTURES.glob("*.json"))
    assert valid_paths, "admin positive fixture set is empty"
    for path in valid_paths:
        document = load_json(path)
        require_valid(validator, document, path.relative_to(ROOT))
        contract = document.get("contract")
        require(isinstance(contract, str), f"positive fixture lacks contract: {path}")
        require(
            contract not in canonical_documents,
            f"duplicate canonical positive fixture for {contract}: {path}",
        )
        canonical_documents[contract] = (path.relative_to(ROOT), document)

    token_redaction = {
        "subjectTokenLogged": False,
        "subjectTokenPersisted": False,
        "accessTokenLogged": False,
        "accessTokenPersisted": False,
        "tokensReturnedInDiagnostics": False,
        "rawEmailsPresent": False,
        "rawBiometricMaterialPresent": False,
    }
    synthetic_exchange_documents = {
        "AdminRevocationTokenExchangeRequest": {
            "contract": "AdminRevocationTokenExchangeRequest",
            "payload": {
                "schema": "ores.shared-auth-admin-revocation-token-exchange-request/v1",
                "requestId": "request-token-exchange-01",
                "subjectToken": "x" * 32,
                "subjectTokenType": "urn:ietf:params:oauth:token-type:access_token",
                "audience": "shared-auth-web-server",
                "requestedScope": "shared-auth:sessions:revoke:global",
                "requestedAt": "2026-08-11T15:01:00Z",
                "redaction": token_redaction,
            },
        },
        "AdminRevocationTokenExchangeResult": {
            "contract": "AdminRevocationTokenExchangeResult",
            "payload": {
                "schema": "ores.shared-auth-admin-revocation-token-exchange-result/v1",
                "requestId": "request-token-exchange-01",
                "accessToken": "y" * 32,
                "issuedTokenType": "urn:ietf:params:oauth:token-type:access_token",
                "tokenType": "Bearer",
                "expiresInSeconds": 120,
                "audience": "shared-auth-web-server",
                "authorizedParty": "shared-auth-web-server",
                "scope": "shared-auth:sessions:revoke:global",
                "issuedAt": "2026-08-11T15:01:01Z",
                "expiresAt": "2026-08-11T15:03:01Z",
                "redaction": token_redaction,
            },
        },
    }
    for contract, document in synthetic_exchange_documents.items():
        require_valid(validator, document, f"in-memory {contract}")
        canonical_documents[contract] = (f"in-memory {contract}", document)

    unsafe_exchange_request = deepcopy(
        synthetic_exchange_documents["AdminRevocationTokenExchangeRequest"]
    )
    unsafe_exchange_request["payload"]["audience"] = "some-other-service"
    require_invalid(validator, unsafe_exchange_request, "wrong exchange audience")
    unsafe_exchange_request = deepcopy(
        synthetic_exchange_documents["AdminRevocationTokenExchangeRequest"]
    )
    unsafe_exchange_request["payload"]["azp"] = "caller-selected"
    require_invalid(validator, unsafe_exchange_request, "caller-selected exchange azp")
    unsafe_exchange_result = deepcopy(
        synthetic_exchange_documents["AdminRevocationTokenExchangeResult"]
    )
    unsafe_exchange_result["payload"]["expiresInSeconds"] = 301
    require_invalid(validator, unsafe_exchange_result, "overlong exchange token lifetime")
    exchange_result_example = synthetic_exchange_documents[
        "AdminRevocationTokenExchangeResult"
    ]["payload"]
    assert timestamp(exchange_result_example["issuedAt"]) < timestamp(
        exchange_result_example["expiresAt"]
    )

    for path in sorted(ADMIN_EXAMPLES.rglob("*.json")) + sorted(
        (ADMIN_SCHEMA.parent / "fixtures").rglob("*.json")
    ):
        source = path.read_text(encoding="utf-8")
        assert '"subjectToken"' not in source, f"subject token field in fixture {path}"
        assert '"accessToken"' not in source, f"access token field in fixture {path}"

    for name, definition in EXAMPLE_DEFINITIONS.items():
        if definition not in REVOCATION_CONTRACTS or definition in canonical_documents:
            continue
        document = {"contract": definition, "payload": examples[name]}
        canonical_documents[definition] = (f"generated envelope for {name}", document)

    coverage = Counter(canonical_documents.keys())
    assert coverage == Counter(ADMIN_CONTRACTS), (
        f"positive fixtures must cover every discriminator exactly once: {coverage!r}"
    )

    legacy_validator = Draft202012Validator(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "contract": {"enum": list(ADMIN_CONTRACTS)},
                "payload": {"type": "object"},
            },
            "required": ["contract", "payload"],
        }
    )
    cross_shape_count = 0
    for source_contract, (source_label, source) in canonical_documents.items():
        for target_contract in ADMIN_CONTRACTS:
            if target_contract == source_contract:
                continue
            candidate = {"contract": target_contract, "payload": source["payload"]}
            assert legacy_validator.is_valid(candidate)
            require(
                not validator.is_valid(candidate),
                f"{source_label} payload unexpectedly validates as {target_contract}",
            )
            cross_shape_count += 1
    assert cross_shape_count == len(ADMIN_CONTRACTS) * (len(ADMIN_CONTRACTS) - 1)

    invalid_paths = sorted(ADMIN_INVALID_FIXTURES.glob("*.json"))
    assert invalid_paths, "admin negative fixture set is empty"
    for path in invalid_paths:
        document = load_json(path)
        assert legacy_validator.is_valid(document), (
            f"negative fixture does not exercise the former loose-payload gap: {path}"
        )
        require_invalid(validator, document, path.relative_to(ROOT))

    for name in REVOCATION_EXAMPLE_NAMES:
        source = (ADMIN_EXAMPLES / name).read_text(encoding="utf-8")
        assert EMAIL_VALUE.search(source) is None, f"raw email-like value in {name}"
        assert_revocation_redaction(examples[name]["redaction"])

    search_result = examples["principal-search-result.json"]
    assert search_result["state"] == "ambiguous"
    assert len(search_result["candidates"]) >= 2
    assert search_result["requiresExplicitPrincipalSelection"] is True
    assert len({candidate["principalId"] for candidate in search_result["candidates"]}) == len(search_result["candidates"])
    assert all(candidate["principalId"] for candidate in search_result["candidates"])
    assert all(
        {"providerTenantId", "opaqueIdentityHandle"} <= set(identity)
        for candidate in search_result["candidates"]
        for identity in candidate["identities"]
    )
    unsafe_search_request = deepcopy(examples["principal-search-request.json"])
    unsafe_search_request["email"] = "forbidden"
    assert not schema_matches(unsafe_search_request, definitions["PrincipalSearchRequest"], schema)
    unresolved_ambiguity = deepcopy(search_result)
    unresolved_ambiguity["candidates"] = unresolved_ambiguity["candidates"][:1]
    assert not schema_matches(unresolved_ambiguity, definitions["PrincipalSearchResult"], schema)

    selection_request_example = canonical_documents["PrincipalSelectionRequest"][1]["payload"]
    selection_result_example = canonical_documents["PrincipalSelectionResult"][1]["payload"]
    preview_request_example = canonical_documents["GlobalRevocationPreviewRequest"][1]["payload"]
    assert selection_request_example["lookupId"] == selection_result_example["lookupId"]
    assert selection_request_example["principalId"] == selection_result_example["principalId"]
    assert selection_request_example["selectionConfirmed"] is True
    assert timestamp(selection_result_example["selectedAt"]) < timestamp(
        selection_result_example["expiresAt"]
    )
    assert preview_request_example["selectionId"] == selection_result_example["selectionId"]
    assert not ({"principalId", "email", "emailSearchKeyHash"} & set(preview_request_example))
    assert {"interactive_sessions", "refresh_token_families"} <= set(
        preview_request_example["selectedScopes"]
    )

    preview_example = examples["global-revocation-preview.json"]
    request_example = examples["global-revocation-request.json"]
    operation_example = examples["global-revocation-operation.json"]
    running_operation_example = examples["global-revocation-operation-running.json"]
    assert preview_example["principalId"] == operation_example["principalId"]
    assert preview_example["previewId"] == request_example["previewId"] == operation_example["previewId"]
    assert preview_example["selectedScopes"] == request_example["selectedScopes"] == operation_example["selectedScopes"]
    assert {"interactive_sessions", "refresh_token_families"} <= set(request_example["selectedScopes"])
    assert timestamp(preview_example["generatedAt"]) < timestamp(preview_example["expiresAt"])
    assert preview_example["blastRadius"]["inventoryStatus"] == "complete"
    assert preview_example["blastRadius"]["unknownFields"] == []

    unavailable_preview = deepcopy(preview_example)
    unavailable_preview["blastRadius"]["inventoryStatus"] = "unavailable"
    unavailable_preview["blastRadius"]["unknownFields"] = sorted(INVENTORY_COUNT_FIELDS)
    for field in INVENTORY_COUNT_FIELDS:
        unavailable_preview["blastRadius"][field] = None
    assert validator.is_valid(
        {"contract": "GlobalRevocationPreview", "payload": unavailable_preview}
    )

    fabricated_zero = deepcopy(unavailable_preview)
    fabricated_zero["blastRadius"]["organizationCount"] = 0
    assert not validator.is_valid(
        {"contract": "GlobalRevocationPreview", "payload": fabricated_zero}
    )
    unreported_unknown = deepcopy(unavailable_preview)
    unreported_unknown["blastRadius"]["unknownFields"].remove("organizationCount")
    assert not validator.is_valid(
        {"contract": "GlobalRevocationPreview", "payload": unreported_unknown}
    )

    partial_preview = deepcopy(preview_example)
    partial_preview["blastRadius"]["inventoryStatus"] = "partial"
    partial_preview["blastRadius"]["organizationCount"] = None
    partial_preview["blastRadius"]["projectCount"] = None
    partial_preview["blastRadius"]["unknownFields"] = [
        "organizationCount",
        "projectCount",
    ]
    assert validator.is_valid(
        {"contract": "GlobalRevocationPreview", "payload": partial_preview}
    )
    commit_authorization_example = canonical_documents[
        "GlobalRevocationCommitAuthorization"
    ][1]["payload"]
    assert request_example["commitAuthorizationId"] == (
        commit_authorization_example["commitAuthorizationId"]
    )
    assert request_example["previewId"] == commit_authorization_example["previewId"]
    assert preview_example["principalId"] == commit_authorization_example["principalId"]
    assert request_example["selectedScopes"] == commit_authorization_example["selectedScopes"]
    assert not ({"principalId", "principalSelectionConfirmed", "stepUp"} & set(request_example))
    verified_step_up = commit_authorization_example["verifiedStepUp"]
    assert timestamp(verified_step_up["verifiedAt"]) <= timestamp(
        commit_authorization_example["issuedAt"]
    )
    assert timestamp(commit_authorization_example["issuedAt"]) <= timestamp(
        commit_authorization_example["expiresAt"]
    )
    assert timestamp(commit_authorization_example["expiresAt"]) <= timestamp(
        verified_step_up["freshUntil"]
    )
    assert timestamp(commit_authorization_example["expiresAt"]) <= timestamp(
        preview_example["expiresAt"]
    )
    assert verified_step_up["assurance"] in {"aal2", "aal3"}
    assert verified_step_up["phishingResistant"] is True
    assert "webauthn" in verified_step_up["authMethods"]
    assert commit_authorization_example["dualControlSatisfied"] is True
    if commit_authorization_example["dualControlRequired"]:
        assert commit_authorization_example["previewCreatedByPrincipalIdHash"] != (
            commit_authorization_example["commitAuthorizedByPrincipalIdHash"]
        )
    client_asserted_step_up = deepcopy(request_example)
    client_asserted_step_up["stepUp"] = verified_step_up
    assert not schema_matches(
        client_asserted_step_up, definitions["GlobalRevocationRequest"], schema
    )

    assert operation_example["state"] == "partial"
    assert operation_example["fence"]["effective"] is True
    assert operation_example["fence"]["authEpoch"] > operation_example["fence"]["previousAuthEpoch"]
    assert timestamp(operation_example["fence"]["appliedAt"]) <= timestamp(operation_example["createdAt"])
    target_states = {target["state"] for target in operation_example["targets"]}
    assert "succeeded" in target_states
    assert target_states & {"failed", "unsupported"}
    assert all(target["attemptCount"] >= 0 for target in operation_example["targets"])
    assert all(not target["retryable"] for target in operation_example["targets"] if target["state"] in {"succeeded", "failed", "skipped", "unsupported"})
    assert all(
        "nextAttemptAt" not in target and "retryAfterSeconds" not in target
        for target in operation_example["targets"]
        if target["state"] in {"succeeded", "failed", "skipped", "unsupported"}
    )
    assert operation_example["audit"]["rawEmailsPresent"] is False
    assert operation_example["audit"]["rawTokensPresent"] is False
    assert operation_example["audit"]["rawBiometricMaterialPresent"] is False
    assert "idempotencyKey" not in operation_example
    retrying_targets = [
        target for target in running_operation_example["targets"]
        if target["state"] == "retry_scheduled"
    ]
    assert len(retrying_targets) == 1
    assert retrying_targets[0]["retryable"] is True
    assert retrying_targets[0]["attemptCount"] > 0
    assert timestamp(retrying_targets[0]["lastAttemptAt"]) < timestamp(retrying_targets[0]["nextAttemptAt"])
    assert retrying_targets[0]["retryAfterSeconds"] > 0
    retry_without_next_attempt = deepcopy(running_operation_example)
    next(
        target for target in retry_without_next_attempt["targets"]
        if target["state"] == "retry_scheduled"
    ).pop("nextAttemptAt")
    assert not schema_matches(retry_without_next_attempt, definitions["GlobalRevocationOperation"], schema)
    retry_without_delay = deepcopy(running_operation_example)
    next(
        target for target in retry_without_delay["targets"]
        if target["state"] == "retry_scheduled"
    ).pop("retryAfterSeconds")
    assert not schema_matches(retry_without_delay, definitions["GlobalRevocationOperation"], schema)
    retry_with_zero_delay = deepcopy(running_operation_example)
    next(
        target for target in retry_with_zero_delay["targets"]
        if target["state"] == "retry_scheduled"
    )["retryAfterSeconds"] = 0
    assert not schema_matches(retry_with_zero_delay, definitions["GlobalRevocationOperation"], schema)
    terminal_with_next_attempt = deepcopy(operation_example)
    next(
        target for target in terminal_with_next_attempt["targets"]
        if target["state"] == "failed"
    )["nextAttemptAt"] = "2026-08-11T15:04:00Z"
    assert not schema_matches(terminal_with_next_attempt, definitions["GlobalRevocationOperation"], schema)
    terminal_with_retry_delay = deepcopy(operation_example)
    next(
        target for target in terminal_with_retry_delay["targets"]
        if target["state"] == "failed"
    )["retryAfterSeconds"] = 30
    assert not schema_matches(terminal_with_retry_delay, definitions["GlobalRevocationOperation"], schema)
    falsely_complete = deepcopy(operation_example)
    for target in falsely_complete["targets"]:
        target["state"] = "succeeded"
        target["retryable"] = False
    assert not schema_matches(falsely_complete, definitions["GlobalRevocationOperation"], schema)
    false_success = deepcopy(operation_example)
    false_success["state"] = "succeeded"
    assert not schema_matches(false_success, definitions["GlobalRevocationOperation"], schema)
    leaked_idempotency_key = deepcopy(operation_example)
    leaked_idempotency_key["idempotencyKey"] = "forbidden_response_value"
    assert not schema_matches(leaked_idempotency_key, definitions["GlobalRevocationOperation"], schema)

    for language, path in LANGUAGE_BINDINGS.items():
        source = path.read_text(encoding="utf-8")
        missing_types = REVOCATION_TYPES - {name for name in REVOCATION_TYPES if name in source}
        assert not missing_types, f"{language} revocation type drift: {sorted(missing_types)}"
        missing_scopes = REVOCATION_SCOPES - {value for value in REVOCATION_SCOPES if value in source}
        assert not missing_scopes, f"{language} revocation scope drift: {sorted(missing_scopes)}"
        missing_states = (REVOCATION_JOB_STATES | REVOCATION_TARGET_STATES) - {
            value for value in REVOCATION_JOB_STATES | REVOCATION_TARGET_STATES if value in source
        }
        assert not missing_states, f"{language} revocation state drift: {sorted(missing_states)}"
        normalized_source = re.sub(r"[^a-z0-9]", "", source.lower())
        missing_fields = {
            field for field in REVOCATION_FIELDS
            if re.sub(r"[^a-z0-9]", "", field.lower()) not in normalized_source
        }
        assert not missing_fields, f"{language} revocation field drift: {sorted(missing_fields)}"
        missing_directory_types = DIRECTORY_ADMIN_TYPES - {
            name for name in DIRECTORY_ADMIN_TYPES if name in source
        }
        assert not missing_directory_types, (
            f"{language} directory admin type drift: {sorted(missing_directory_types)}"
        )
        missing_directory_scopes = DIRECTORY_ADMIN_SCOPES - {
            value for value in DIRECTORY_ADMIN_SCOPES if value in source
        }
        assert not missing_directory_scopes, (
            f"{language} directory admin scope drift: {sorted(missing_directory_scopes)}"
        )
        missing_directory_roles = DIRECTORY_ADMIN_ROLES - {
            value for value in DIRECTORY_ADMIN_ROLES if value in source
        }
        assert not missing_directory_roles, (
            f"{language} directory admin role drift: {sorted(missing_directory_roles)}"
        )
        missing_directory_fields = {
            field for field in DIRECTORY_ADMIN_FIELDS
            if re.sub(r"[^a-z0-9]", "", field.lower()) not in normalized_source
        }
        assert not missing_directory_fields, (
            f"{language} directory admin field drift: {sorted(missing_directory_fields)}"
        )


def validate_shared_auth_contract() -> None:
    schema = json.loads(SHARED_AUTH_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    definitions = schema["$defs"]
    assert {
        "Organization",
        "Project",
        "User",
        "Membership",
        "Role",
        "RoleBinding",
        "Session",
        "Factor",
        "AuditEvent",
        "RevokeSessionsByEmailRequest",
        "RevokeSessionsByEmailResult",
    } <= set(definitions)

    factor = definitions["Factor"]
    assert "privateKey" not in factor["properties"]
    assert "biometricTemplate" not in factor["properties"]
    assert factor["properties"]["privateKeyMaterialPresent"]["const"] is False
    assert factor["properties"]["rawBiometricMaterialPresent"]["const"] is False

    request = definitions["RevokeSessionsByEmailRequest"]
    normalized_email = request["properties"]["normalizedEmail"]
    assert normalized_email["writeOnly"] is True
    assert normalized_email["pattern"].startswith("^[a-z0-9")
    assert {"idempotencyKey", "normalizedEmail", "scope", "reason"} <= set(
        request["required"]
    )

    result = definitions["RevokeSessionsByEmailResult"]
    assert "normalizedEmail" not in result["properties"]
    assert "email" not in result["properties"]
    assert result["properties"]["authorizationPolicy"]["const"] == (
        "per_organization_sessions.revoke"
    )
    assert (
        result["properties"]["onlyAuthorizedOrganizationsProcessed"]["const"]
        is True
    )
    organization_result = definitions["OrganizationRevocationResult"]
    assert organization_result["properties"]["authorizationVerified"]["const"] is True

    request_example = json.loads(REVOCATION_REQUEST_EXAMPLE.read_text(encoding="utf-8"))
    result_example = json.loads(REVOCATION_RESULT_EXAMPLE.read_text(encoding="utf-8"))
    assert request_example["normalizedEmail"] == request_example["normalizedEmail"].lower()
    assert len(request_example["idempotencyKey"]) >= 16
    assert "normalizedEmail" not in result_example and "email" not in result_example
    assert result_example["onlyAuthorizedOrganizationsProcessed"] is True
    assert all(
        item["authorizationVerified"] is True
        for item in result_example["organizationResults"]
    )

    platform_schema = ROOT / "contracts/ores-platform/v1/schema.json"
    assert platform_schema.is_file()
    binding_manifest = json.loads(
        (SHARED_AUTH_SCHEMA.parent / "bindings.json").read_text(encoding="utf-8")
    )
    assert binding_manifest["source"] == "contracts/shared-auth/v1/schema.json"
    assert {item["language"] for item in binding_manifest["bindings"]} == {
        "rust",
        "typescript",
        "go",
        "dart",
    }
    for binding in binding_manifest["bindings"]:
        assert binding["maintenance"] == "hand-maintained"
        source = (ROOT / binding["path"]).read_text(encoding="utf-8")
        for name in binding_manifest["requiredTypes"]:
            assert name in source, f"{binding['language']} binding missing {name}"

def main() -> int:
    document = json.loads(PLATFORM_SCHEMA.read_text(encoding="utf-8"))
    assert document["$schema"].endswith("2020-12/schema")
    methods = set(document["$defs"]["AuthMethod"]["enum"])
    assert methods == AUTH_METHODS, (methods, AUTH_METHODS)
    proof = document["$defs"]["PlatformBiometricProof"]["properties"]
    assert proof["rawBiometricMaterialPresent"]["const"] is False

    validate_admin_contract()
    validate_shared_auth_contract()

    zpkg = (ROOT / ".zpkg.toml").read_text(encoding="utf-8")
    assert '[targets.shared-auth-contracts]' in zpkg
    assert 'dir = "contracts/shared-auth"' in zpkg
    # ores.otel.log depends on this foundational package; adding the reverse edge is a cycle.
    assert '"oresoftware/next-loggers"' not in zpkg

    present = {path.name for path in (ROOT / "langs").iterdir() if path.is_dir()}
    assert LANGUAGES <= present, LANGUAGES - present
    for path in ROOT.rglob("*"):
        if path.resolve() == pathlib.Path(__file__).resolve():
            continue
        if any(part in SKIP_PARTS for part in path.parts) or path.suffix in SKIP_SUFFIXES:
            continue
        if path.is_file() and path.stat().st_size < 2_000_000:
            text = path.read_text(encoding="utf-8", errors="ignore")
            match = FORBIDDEN.search(text)
            if match:
                raise AssertionError(
                    f"forbidden secret/biometric material marker in {path}: {match.group(0)}"
                )
    print(
        "contracts valid: "
        f"methods={len(methods)} languages={len(present)} revocation_scopes={len(REVOCATION_SCOPES)} "
        "admin_contract=shared-auth-admin/v1 domain_contract=shared-auth/v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
