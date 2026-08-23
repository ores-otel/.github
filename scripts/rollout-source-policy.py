#!/usr/bin/env python3
"""Roll out the immutable source-policy caller workflow across reviewed organizations."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
API_ROOT = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
USER_AGENT = "ores-source-policy-rollout/1"
WORKFLOW_PATH = ".github/workflows/source-policy-lint.yml"
MANAGED_HEADER = "# Managed by ores-otel source-policy fleet rollout."
REQUIRED_POLICY_PATHS = (
    ".github/workflows/source-policy-lint.yml",
    "tools/ecmascript-lint/lint.mjs",
    "tools/ecmascript-lint/package-lock.json",
    "tools/rust-explicit-return/Cargo.lock",
    "tools/rust-explicit-return/src/main.rs",
)


@dataclass(frozen=True)
class Target:
    full_name: str
    default_branch: str
    languages: tuple[str, ...]
    pushed_at: str


@dataclass(frozen=True)
class Result:
    full_name: str
    state: str
    detail: str
    commit_sha: str | None = None


class GitHub:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{API_ROOT}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": USER_AGENT,
                **({"Content-Type": "application/json"} if data is not None else {}),
            },
        )

        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    raw = response.read()
                    return response.status, json.loads(raw) if raw else None
            except urllib.error.HTTPError as error:
                raw = error.read()
                try:
                    payload: Any = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    payload = raw.decode("utf-8", errors="replace")
                if error.code not in {429, 500, 502, 503, 504} or attempt == 3:
                    return error.code, payload
            except urllib.error.URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"GitHub request failed: {error}") from error
            time.sleep(2**attempt)

        raise AssertionError("request retry loop exhausted")

    def require(self, method: str, path: str, expected: set[int]) -> Any:
        status, payload = self.request(method, path)
        if status not in expected:
            raise RuntimeError(f"{method} {path} failed with HTTP {status}: {payload}")
        return payload

    def organization_repositories(self, organization: str) -> list[dict[str, Any]]:
        encoded = urllib.parse.quote(organization, safe="")
        repositories: list[dict[str, Any]] = []
        for page in range(1, 101):
            path = (
                f"/orgs/{encoded}/repos?per_page=100&type=all&sort=pushed"
                f"&direction=desc&page={page}"
            )
            payload = self.require("GET", path, {200})
            repositories.extend(payload)
            if len(payload) < 100:
                return repositories
        raise RuntimeError(
            f"repository pagination exceeded safety bound for {organization}"
        )

    def languages(self, full_name: str) -> tuple[str, ...]:
        payload = self.require("GET", f"/repos/{full_name}/languages", {200})
        return tuple(sorted(payload))

    def content(
        self,
        full_name: str,
        path: str,
        ref: str,
    ) -> tuple[str, str] | None:
        encoded_ref = urllib.parse.quote(ref, safe="")
        status, payload = self.request(
            "GET", f"/repos/{full_name}/contents/{path}?ref={encoded_ref}"
        )
        if status == 404:
            return None
        if status != 200:
            raise RuntimeError(
                f"GET {full_name}/{path}@{ref} failed with HTTP {status}: {payload}"
            )
        if payload.get("type") != "file" or payload.get("encoding") != "base64":
            raise RuntimeError(f"unexpected content response for {full_name}/{path}")
        decoded = base64.b64decode(payload["content"].replace("\n", "")).decode("utf-8")
        return payload["sha"], decoded

    def put_content(
        self,
        target: Target,
        desired: str,
        current_sha: str | None,
    ) -> str:
        body: dict[str, Any] = {
            "message": "ci: add pre-build JS and Rust source lint",
            "content": base64.b64encode(desired.encode("utf-8")).decode("ascii"),
            "branch": target.default_branch,
        }
        if current_sha is not None:
            body["sha"] = current_sha

        status, payload = self.request(
            "PUT", f"/repos/{target.full_name}/contents/{WORKFLOW_PATH}", body
        )
        if status not in {200, 201}:
            raise RuntimeError(
                f"PUT {target.full_name}/{WORKFLOW_PATH} failed with HTTP {status}: {payload}"
            )
        return payload["commit"]["sha"]


def token_from_environment_or_gh() -> str:
    token = os.environ.get("SOURCE_POLICY_GITHUB_TOKEN")
    if token:
        return token
    try:
        return subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise RuntimeError(
            "set SOURCE_POLICY_GITHUB_TOKEN or authenticate the GitHub CLI"
        ) from error


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "excludedRepositories",
        "fleetVersion",
        "languages",
        "minimumOrganizations",
        "minimumRepositories",
        "organizations",
        "repositoriesPerOrganization",
    }
    missing = required.difference(manifest)
    if missing:
        raise RuntimeError(f"manifest is missing fields: {', '.join(sorted(missing))}")
    if len(set(manifest["organizations"])) != len(manifest["organizations"]):
        raise RuntimeError("manifest contains duplicate organizations")
    if manifest["minimumRepositories"] < 90 or manifest["minimumOrganizations"] < 20:
        raise RuntimeError(
            "manifest weakens the reviewed 90-repository/20-organization floor"
        )
    return manifest


def select_targets(
    github: GitHub,
    manifest: dict[str, Any],
    organization_filter: set[str],
) -> list[Target]:
    wanted_languages = set(manifest["languages"])
    exclusions = set(manifest["excludedRepositories"])
    per_organization = manifest["repositoriesPerOrganization"]
    targets: list[Target] = []

    organizations = manifest["organizations"]
    if organization_filter:
        unknown = organization_filter.difference(organizations)
        if unknown:
            raise RuntimeError(
                f"unknown organization filter(s): {', '.join(sorted(unknown))}"
            )
        organizations = [org for org in organizations if org in organization_filter]

    for organization in organizations:
        selected = 0
        for repository in github.organization_repositories(organization):
            full_name = repository["full_name"]
            if full_name in exclusions:
                continue
            if repository["archived"] or repository["disabled"] or repository["fork"]:
                continue
            if not repository.get("default_branch"):
                continue
            permissions = repository.get("permissions", {})
            if permissions and not permissions.get("push", False):
                continue

            languages = github.languages(full_name)
            if wanted_languages.isdisjoint(languages):
                continue

            targets.append(
                Target(
                    full_name=full_name,
                    default_branch=repository["default_branch"],
                    languages=languages,
                    pushed_at=repository.get("pushed_at") or "",
                )
            )
            selected += 1
            if selected == per_organization:
                break

        print(f"selected {selected}: {organization}", file=sys.stderr)

    return targets


def render_caller_workflow(policy_sha: str, default_branch: str) -> str:
    quoted_branch = json.dumps(default_branch)
    return f"""{MANAGED_HEADER}
name: Pre-build source policy lint

on:
  pull_request:
  push:
    branches: [{quoted_branch}]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  source-policy:
    uses: ores-otel/.github/.github/workflows/source-policy-lint.yml@{policy_sha}
    permissions:
      contents: read
"""


def verify_policy_commit(github: GitHub, policy_sha: str) -> None:
    for path in REQUIRED_POLICY_PATHS:
        if github.content("ores-otel/.github", path, policy_sha) is None:
            raise RuntimeError(f"policy commit {policy_sha} is missing {path}")


def inspect_or_apply(
    github: GitHub,
    target: Target,
    policy_sha: str,
    apply: bool,
) -> Result:
    desired = render_caller_workflow(policy_sha, target.default_branch)
    current = github.content(
        target.full_name,
        WORKFLOW_PATH,
        target.default_branch,
    )
    if current is not None and current[1] == desired:
        return Result(target.full_name, "unchanged", "already matches immutable policy")
    if current is not None and not current[1].startswith(MANAGED_HEADER):
        return Result(
            target.full_name, "conflict", "existing workflow is not fleet-managed"
        )
    if not apply:
        state = "would-update" if current is not None else "would-create"
        return Result(target.full_name, state, target.default_branch)

    commit_sha = github.put_content(
        target,
        desired,
        current[0] if current is not None else None,
    )
    verified = github.content(target.full_name, WORKFLOW_PATH, target.default_branch)
    if verified is None or verified[1] != desired:
        raise RuntimeError(f"post-write verification failed for {target.full_name}")
    state = "updated" if current is not None else "created"
    return Result(target.full_name, state, target.default_branch, commit_sha)


def validate_coverage(
    targets: list[Target],
    manifest: dict[str, Any],
    organization_filter: set[str],
) -> None:
    if organization_filter:
        return
    organization_count = len({target.full_name.split("/", 1)[0] for target in targets})
    if len(targets) < manifest["minimumRepositories"]:
        raise RuntimeError(
            f"selected {len(targets)} repositories; minimum is {manifest['minimumRepositories']}"
        )
    if organization_count < manifest["minimumOrganizations"]:
        raise RuntimeError(
            f"selected {organization_count} organizations; "
            f"minimum is {manifest['minimumOrganizations']}"
        )


def print_report(
    policy_sha: str,
    targets: list[Target],
    results: list[Result],
    failures: list[Result],
) -> None:
    organizations = sorted({target.full_name.split("/", 1)[0] for target in targets})
    report = {
        "policySha": policy_sha,
        "repositoryCount": len(targets),
        "organizationCount": len(organizations),
        "organizations": organizations,
        "states": {
            state: sum(result.state == state for result in [*results, *failures])
            for state in sorted({result.state for result in [*results, *failures]})
        },
        "results": [
            {
                "repository": result.full_name,
                "state": result.state,
                "detail": result.detail,
                **({"commitSha": result.commit_sha} if result.commit_sha else {}),
            }
            for result in [*results, *failures]
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "source-policy-fleet.json",
    )
    parser.add_argument("--policy-sha", required=True)
    parser.add_argument("--organization", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.policy_sha):
        raise RuntimeError(
            "--policy-sha must be a full lowercase 40-character commit SHA"
        )

    manifest = load_manifest(args.manifest)
    github = GitHub(token_from_environment_or_gh())
    verify_policy_commit(github, args.policy_sha)
    organization_filter = set(args.organization)
    targets = select_targets(github, manifest, organization_filter)
    validate_coverage(targets, manifest, organization_filter)

    results: list[Result] = []
    failures: list[Result] = []
    for target in targets:
        try:
            result = inspect_or_apply(github, target, args.policy_sha, args.apply)
            results.append(result)
            print(f"{result.state}: {result.full_name}", file=sys.stderr)
        except (
            Exception
        ) as error:  # Continue to produce a complete fleet exception report.
            failure = Result(target.full_name, "failed", str(error))
            failures.append(failure)
            print(f"failed: {target.full_name}: {error}", file=sys.stderr)

    print_report(args.policy_sha, targets, results, failures)
    conflicts = [result for result in results if result.state == "conflict"]
    return 1 if failures or conflicts else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"source-policy rollout failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
