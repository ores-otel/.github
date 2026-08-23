#!/usr/bin/env python3
"""Audit or open pull requests for the immutable source-policy caller workflow."""

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
USER_AGENT = "ores-source-policy-rollout/2"
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
    pull_request_url: str | None = None


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

    def branch_sha(self, full_name: str, branch: str) -> str:
        encoded_branch = urllib.parse.quote(branch, safe="")
        payload = self.require(
            "GET", f"/repos/{full_name}/git/ref/heads/{encoded_branch}", {200}
        )
        return payload["object"]["sha"]

    def create_branch(self, target: Target, branch: str) -> str:
        base_sha = self.branch_sha(target.full_name, target.default_branch)
        body = {"ref": f"refs/heads/{branch}", "sha": base_sha}
        status, payload = self.request(
            "POST", f"/repos/{target.full_name}/git/refs", body
        )
        if status == 201:
            return payload["object"]["sha"]
        if status == 422:
            return self.branch_sha(target.full_name, branch)
        raise RuntimeError(
            f"POST {target.full_name}/git/refs failed with HTTP {status}: {payload}"
        )

    def put_content(
        self,
        target: Target,
        branch: str,
        desired: str,
        current_sha: str | None,
    ) -> str:
        body: dict[str, Any] = {
            "message": "ci: add pre-build JS and Rust source lint",
            "content": base64.b64encode(desired.encode("utf-8")).decode("ascii"),
            "branch": branch,
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

    def open_pull_request(
        self,
        target: Target,
        branch: str,
        policy_sha: str,
    ) -> str:
        body = {
            "title": "ci: adopt Ores source policy v2",
            "head": branch,
            "base": target.default_branch,
            "body": (
                "Adopt the warn-first `ores-source-policy/v2` workflow at immutable "
                f"commit `{policy_sha}`.\n\n"
                "The policy reports JavaScript/TypeScript semicolon omissions, Rust "
                "implicit returns, and likely Ores telemetry chains that omit their "
                "terminal `.send()` call. It does not rewrite source and parser/source "
                "access errors are the only enforcement failures.\n\n"
                "Tracks https://github.com/ORESoftware/k8s-cluster/issues/1400"
            ),
        }
        status, payload = self.request(
            "POST", f"/repos/{target.full_name}/pulls", body
        )
        if status == 201:
            return payload["html_url"]
        if status != 422:
            raise RuntimeError(
                f"POST {target.full_name}/pulls failed with HTTP {status}: {payload}"
            )

        owner = target.full_name.split("/", 1)[0]
        encoded_head = urllib.parse.quote(f"{owner}:{branch}", safe="")
        encoded_base = urllib.parse.quote(target.default_branch, safe="")
        existing = self.require(
            "GET",
            f"/repos/{target.full_name}/pulls?state=open&head={encoded_head}&base={encoded_base}",
            {200},
        )
        if existing:
            return existing[0]["html_url"]
        raise RuntimeError(
            f"GitHub rejected the pull request and no matching open PR exists: {payload}"
        )

    def existing_managed_rollout_pull_request(
        self, target: Target
    ) -> tuple[str, str] | None:
        pull_requests = self.require(
            "GET", f"/repos/{target.full_name}/pulls?state=open&per_page=100", {200}
        )
        accepted_titles = {
            "ci: add shared source policy lint",
            "ci: adopt Ores source policy v2",
        }
        for pull_request in pull_requests:
            if pull_request.get("title") not in accepted_titles:
                continue
            head = pull_request.get("head") or {}
            head_repository = head.get("repo") or {}
            if head_repository.get("full_name") != target.full_name:
                continue
            branch = head.get("ref")
            if not branch:
                continue
            content = self.content(target.full_name, WORKFLOW_PATH, branch)
            if content is not None and content[1].startswith(MANAGED_HEADER):
                return branch, pull_request["html_url"]
        return None


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
        "inlineWorkflowRepositories",
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


def render_inline_caller_workflow(policy_sha: str, default_branch: str) -> str:
    quoted_branch = json.dumps(default_branch)
    return f"""{MANAGED_HEADER}
# This repository prohibits outbound reusable workflows. Keep the same
# immutable central policy implementation wired as ordinary job steps.
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
    name: ESLint and Rust source policy
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Check out caller repository
        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
        with:
          persist-credentials: false

      - name: Detect tracked source languages
        id: languages
        shell: bash
        run: |
          ecma_files=$(git ls-files -- '*.cjs' '*.mjs' '*.js' '*.jsx' '*.ts' '*.tsx')
          rust_files=$(git ls-files -- '*.rs')
          if [[ -n "$ecma_files" ]]; then
            echo 'ecmascript=true' >> "$GITHUB_OUTPUT"
          else
            echo 'ecmascript=false' >> "$GITHUB_OUTPUT"
          fi
          if [[ -n "$rust_files" ]]; then
            echo 'rust=true' >> "$GITHUB_OUTPUT"
          else
            echo 'rust=false' >> "$GITHUB_OUTPUT"
          fi

      - name: Check out immutable policy implementation
        if: steps.languages.outputs.ecmascript == 'true' || steps.languages.outputs.rust == 'true'
        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
        with:
          repository: ores-otel/.github
          ref: {policy_sha}
          path: .source-policy
          persist-credentials: false

      - name: Set up Node.js
        if: steps.languages.outputs.ecmascript == 'true'
        uses: actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38 # v6
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: .source-policy/tools/ecmascript-lint/package-lock.json

      - name: Install pinned ESLint policy dependencies
        if: steps.languages.outputs.ecmascript == 'true'
        shell: bash
        run: npm ci --ignore-scripts --prefix .source-policy/tools/ecmascript-lint

      - name: Lint ECMAScript source policy
        if: steps.languages.outputs.ecmascript == 'true'
        shell: bash
        run: node .source-policy/tools/ecmascript-lint/lint.mjs "$GITHUB_WORKSPACE"

      - name: Set up stable Rust
        if: steps.languages.outputs.rust == 'true'
        shell: bash
        run: rustup toolchain install 1.88.0 --profile minimal --no-self-update

      - name: Lint Rust source policy
        if: steps.languages.outputs.rust == 'true'
        shell: bash
        env:
          CARGO_TARGET_DIR: ${{{{ runner.temp }}}}/ores-fleet-rust-target
        run: >-
          cargo +1.88.0 run --locked --quiet --release
          --manifest-path .source-policy/tools/rust-explicit-return/Cargo.toml
          -- "$GITHUB_WORKSPACE"

      - name: Report repositories without applicable source
        if: steps.languages.outputs.ecmascript != 'true' && steps.languages.outputs.rust != 'true'
        shell: bash
        run: echo 'No tracked ECMAScript or Rust source files were found.'
"""


def verify_policy_commit(github: GitHub, policy_sha: str) -> None:
    for path in REQUIRED_POLICY_PATHS:
        if github.content("ores-otel/.github", path, policy_sha) is None:
            raise RuntimeError(f"policy commit {policy_sha} is missing {path}")


def inspect_or_open_pull_request(
    github: GitHub,
    target: Target,
    policy_sha: str,
    open_pull_requests: bool,
    inline_workflow: bool,
) -> Result:
    render = (
        render_inline_caller_workflow if inline_workflow else render_caller_workflow
    )
    desired = render(policy_sha, target.default_branch)
    default_content = github.content(
        target.full_name,
        WORKFLOW_PATH,
        target.default_branch,
    )
    if default_content is not None and default_content[1] == desired:
        return Result(
            target.full_name,
            "adopted",
            "default branch matches immutable policy",
            github.branch_sha(target.full_name, target.default_branch),
        )
    if default_content is not None and not default_content[1].startswith(MANAGED_HEADER):
        return Result(
            target.full_name, "conflict", "existing workflow is not fleet-managed"
        )
    existing_pull_request = github.existing_managed_rollout_pull_request(target)
    if not open_pull_requests:
        if existing_pull_request is not None:
            branch, pull_request_url = existing_pull_request
            branch_content = github.content(target.full_name, WORKFLOW_PATH, branch)
            if branch_content is not None and branch_content[1] == desired:
                return Result(
                    target.full_name,
                    "pr-open",
                    branch,
                    github.branch_sha(target.full_name, branch),
                    pull_request_url,
                )
        state = "would-update" if default_content is not None else "would-create"
        return Result(target.full_name, state, target.default_branch)

    if existing_pull_request is None:
        branch = f"agent/source-policy-v2-{policy_sha[:12]}"
        github.create_branch(target, branch)
    else:
        branch = existing_pull_request[0]
    branch_content = github.content(target.full_name, WORKFLOW_PATH, branch)
    if branch_content is not None and not branch_content[1].startswith(MANAGED_HEADER):
        return Result(
            target.full_name,
            "conflict",
            f"{branch} contains a non-fleet-managed workflow",
        )

    commit_sha = github.branch_sha(target.full_name, branch)
    if branch_content is None or branch_content[1] != desired:
        commit_sha = github.put_content(
            target,
            branch,
            desired,
            branch_content[0] if branch_content is not None else None,
        )
    verified = github.content(target.full_name, WORKFLOW_PATH, branch)
    if verified is None or verified[1] != desired:
        raise RuntimeError(
            f"pull-request branch verification failed after commit {commit_sha}"
        )
    pull_request_url = (
        existing_pull_request[1]
        if existing_pull_request is not None
        else github.open_pull_request(target, branch, policy_sha)
    )
    return Result(
        target.full_name,
        "pr-open",
        branch,
        commit_sha,
        pull_request_url,
    )


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
                **(
                    {"pullRequestUrl": result.pull_request_url}
                    if result.pull_request_url
                    else {}
                ),
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
    parser.add_argument(
        "--open-prs",
        action="store_true",
        help="create/update a dedicated branch and open a pull request per target",
    )
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
    inline_repositories = set(manifest["inlineWorkflowRepositories"])

    results: list[Result] = []
    failures: list[Result] = []
    for target in targets:
        try:
            result = inspect_or_open_pull_request(
                github,
                target,
                args.policy_sha,
                args.open_prs,
                target.full_name in inline_repositories,
            )
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
