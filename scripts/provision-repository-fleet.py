#!/usr/bin/env python3
"""Idempotently create, seed, and verify the reviewed ores-otel repository fleet."""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
API_ROOT = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
USER_AGENT = "ores-otel-repository-provisioner/2"


def request(
    token: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            payload: Any = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw.decode("utf-8", errors="replace")
        return error.code, payload


def repo(token: str, full_name: str) -> dict[str, Any] | None:
    status, payload = request(token, "GET", f"/repos/{full_name}")
    if status == 200:
        return payload
    if status == 404:
        return None
    raise RuntimeError(f"GET {full_name} failed with HTTP {status}: {payload}")


def ensure_repo(
    token: str,
    organization: str,
    spec: dict[str, Any],
    visibility: str,
) -> dict[str, Any]:
    full_name = f"{organization}/{spec['name']}"
    existing = repo(token, full_name)
    if existing is not None:
        print(f"exists: {full_name}")
        return existing

    status, payload = request(
        token,
        "POST",
        f"/orgs/{organization}/repos",
        {
            "name": spec["name"],
            "description": spec["description"],
            "visibility": visibility,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "has_discussions": False,
            "auto_init": bool(spec.get("autoInit", False)),
            "delete_branch_on_merge": True,
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
        },
    )
    if status != 201:
        raise RuntimeError(f"create {full_name} failed with HTTP {status}: {payload}")
    print(f"created: {full_name}")
    return payload


def put_text_file(
    token: str,
    full_name: str,
    path: str,
    text: str,
    message: str,
) -> None:
    desired = text.encode("utf-8")
    status, current = request(token, "GET", f"/repos/{full_name}/contents/{path}?ref=main")
    body: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(desired).decode("ascii"),
        "branch": "main",
    }
    if status == 200:
        if current.get("encoding") == "base64":
            present = base64.b64decode(current["content"].replace("\n", ""))
            if present == desired:
                print(f"unchanged: {full_name}/{path}")
                return
        body["sha"] = current["sha"]
    elif status != 404:
        raise RuntimeError(f"read {full_name}/{path} failed with HTTP {status}: {current}")

    write_status, payload = request(token, "PUT", f"/repos/{full_name}/contents/{path}", body)
    if write_status not in (200, 201):
        raise RuntimeError(f"write {full_name}/{path} failed with HTTP {write_status}: {payload}")
    print(f"seeded: {full_name}/{path}")


def conformance_workflow() -> str:
    return """name: Exact-head contract conformance

on:
  workflow_dispatch:
    inputs:
      canonical_sha:
        description: Exact commit SHA in ores-otel/ores.otel.log
        required: true
        type: string
      legacy_sha:
        description: Exact commit SHA in ORESoftware/next-loggers.ts
        required: true
        type: string
  repository_dispatch:
    types: [ores-otel-conformance]

permissions:
  contents: read

jobs:
  contracts:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        include:
          - repository: ores-otel/ores.otel.log
            ref: ${{ inputs.canonical_sha || github.event.client_payload.canonical_sha }}
            role: canonical
          - repository: ORESoftware/next-loggers.ts
            ref: ${{ inputs.legacy_sha || github.event.client_payload.legacy_sha }}
            role: legacy
    steps:
      - name: Validate exact SHA input
        env:
          SOURCE_SHA: ${{ matrix.ref }}
        run: '[[ "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]'
      - name: Fetch exact source
        env:
          SOURCE_REPOSITORY: ${{ matrix.repository }}
          SOURCE_SHA: ${{ matrix.ref }}
        run: |
          git init source
          git -C source remote add origin "https://github.com/${SOURCE_REPOSITORY}.git"
          git -C source fetch --no-tags --depth=1 origin "$SOURCE_SHA"
          test "$(git -C source rev-parse FETCH_HEAD)" = "$SOURCE_SHA"
          git -C source checkout --detach "$SOURCE_SHA"
      - name: Install contract validator
        run: python -m pip install --disable-pip-version-check jsonschema==4.26.0 referencing==0.37.0
      - name: Validate canonical contracts
        working-directory: source
        run: python scripts/validate-contracts.py
      - name: Record tested source
        run: printf '%s %s\n' '${{ matrix.role }}' '${{ matrix.ref }}'
"""


def seed_test_repo(token: str, organization: str, spec: dict[str, Any]) -> None:
    full_name = f"{organization}/{spec['name']}"
    metadata = {
        "matrixVersion": "ores.otel.test-repository/v1",
        **spec,
        "sources": ["ores-otel/ores.otel.log", "ORESoftware/next-loggers.ts"],
        "requireExactHeadChecks": True,
        "requireNoMonkeyPatching": True,
        "status": "seeded",
    }
    readme = (
        f"# {spec['name']}\n\n"
        f"Exact-head **{spec['language']}** conformance harness for "
        "`ores-otel/ores.otel.log` and `ORESoftware/next-loggers.ts`.\n\n"
        f"Native verification command: `{spec['testCommand']}`.\n\n"
        "Promotion requires both sources to pass at explicit 40-character commit SHAs.\n"
    )
    put_text_file(token, full_name, "README.md", readme, "Document conformance harness")
    put_text_file(
        token,
        full_name,
        "conformance.json",
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        "Add conformance metadata",
    )
    put_text_file(
        token,
        full_name,
        ".github/workflows/conformance.yml",
        conformance_workflow(),
        "Add exact-head contract workflow",
    )


def run_git(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        env=env,
        capture_output=capture,
    )


def parse_ref_lines(text: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        sha, ref = line.split(maxsplit=1)
        if ref.endswith("^{}"):
            continue
        refs[ref] = sha
    return refs


def mirror_history(token: str, source: str, destination: str) -> None:
    with tempfile.TemporaryDirectory(prefix="ores-otel-mirror-") as directory:
        root = Path(directory)
        mirror = root / "legacy.git"
        askpass = root / "askpass.sh"
        askpass.write_text(
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  *Username*) printf '%s\\n' x-access-token ;;\n"
            "  *Password*) printf '%s\\n' \"$GH_ADMIN_TOKEN\" ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        askpass.chmod(0o700)
        env = os.environ.copy()
        env.update(
            {
                "GIT_ASKPASS": str(askpass),
                "GIT_TERMINAL_PROMPT": "0",
                "GH_ADMIN_TOKEN": token,
            }
        )

        run_git(["git", "clone", "--mirror", f"https://github.com/{source}.git", str(mirror)])
        destination_url = f"https://github.com/{destination}.git"
        run_git(
            [
                "git",
                "-C",
                str(mirror),
                "push",
                destination_url,
                "+refs/heads/*:refs/heads/*",
                "+refs/tags/*:refs/tags/*",
            ],
            env=env,
        )

        source_result = run_git(
            [
                "git",
                "-C",
                str(mirror),
                "for-each-ref",
                "--format=%(objectname) %(refname)",
                "refs/heads",
                "refs/tags",
            ],
            capture=True,
        )
        destination_result = run_git(
            ["git", "ls-remote", destination_url, "refs/heads/*", "refs/tags/*"],
            env=env,
            capture=True,
        )
        source_refs = parse_ref_lines(source_result.stdout)
        destination_refs = parse_ref_lines(destination_result.stdout)
        missing = sorted(set(source_refs) - set(destination_refs))
        moved = sorted(
            ref
            for ref in set(source_refs) & set(destination_refs)
            if source_refs[ref] != destination_refs[ref]
        )
        extras = sorted(set(destination_refs) - set(source_refs))
        if missing or moved:
            raise RuntimeError(
                "head/tag mirror verification failed: "
                f"missing={missing}, moved={moved}"
            )
        if extras:
            print(
                "preserved destination-only heads/tags: "
                + ", ".join(extras)
            )

        if "refs/heads/main" in source_refs:
            status, payload = request(token, "PATCH", f"/repos/{destination}", {"default_branch": "main"})
            if status != 200:
                raise RuntimeError(
                    f"set default branch for {destination} failed with HTTP {status}: {payload}"
                )

        print(
            f"verified Git head/tag parity: {source} -> {destination}; "
            f"refs={len(source_refs)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--token-env", default="GH_ADMIN_TOKEN")
    parser.add_argument("--skip-history-mirror", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        print(f"required token environment variable is empty: {args.token_env}", file=sys.stderr)
        return 78

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    visibility = manifest["visibility"]
    canonical = manifest["canonical"]
    canonical_spec = {
        "name": canonical["name"],
        "description": canonical["description"],
        "autoInit": canonical["autoInit"],
    }
    ensure_repo(token, canonical["organization"], canonical_spec, visibility)
    canonical_full_name = f"{canonical['organization']}/{canonical['name']}"

    test_org = manifest["testOrganization"]
    for test_spec in manifest["testRepositories"]:
        repo_spec = {
            "name": test_spec["name"],
            "description": (
                f"{test_spec['language']} conformance for canonical and legacy "
                "ores.otel.log sources"
            ),
            "autoInit": True,
        }
        ensure_repo(token, test_org, repo_spec, visibility)
        seed_test_repo(token, test_org, test_spec)

    if not args.skip_history_mirror:
        mirror_history(token, canonical["mirrorFrom"], canonical_full_name)

    print(
        f"fleet ready: canonical={canonical_full_name}; "
        f"test_repositories={len(manifest['testRepositories'])}; "
        f"languages={len({entry['language'] for entry in manifest['testRepositories']})}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
