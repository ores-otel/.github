#!/usr/bin/env python3
"""Idempotently provision the reviewed polyglot shared repositories."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
API_ROOT = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
USER_AGENT = "ores-otel-shared-repository-provisioner/1"
MANIFEST_PATH = ".ores-template-manifest.json"


def request(
    token: str,
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
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
    )
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
        return error.code, payload


def encoded(path: str) -> str:
    return "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))


def get_repo(token: str, full_name: str) -> dict[str, Any] | None:
    status, payload = request(token, "GET", f"/repos/{full_name}")
    if status == 200:
        return payload
    if status == 404:
        return None
    raise RuntimeError(f"GET {full_name} failed with HTTP {status}: {payload}")


def configure_repo(token: str, full_name: str, spec: dict[str, Any]) -> None:
    status, payload = request(
        token,
        "PATCH",
        f"/repos/{full_name}",
        {
            "description": spec["description"],
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "has_discussions": False,
            "delete_branch_on_merge": True,
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
        },
    )
    if status != 200:
        raise RuntimeError(f"configure {full_name} failed with HTTP {status}: {payload}")
    topic_status, topic_payload = request(
        token,
        "PUT",
        f"/repos/{full_name}/topics",
        {"names": sorted(set(spec.get("topics", [])))},
    )
    if topic_status != 200:
        raise RuntimeError(f"topics {full_name} failed with HTTP {topic_status}: {topic_payload}")


def ensure_repo(token: str, spec: dict[str, Any], visibility: str) -> str:
    full_name = f"{spec['organization']}/{spec['name']}"
    if get_repo(token, full_name) is None:
        status, payload = request(
            token,
            "POST",
            f"/orgs/{spec['organization']}/repos",
            {
                "name": spec["name"],
                "description": spec["description"],
                "visibility": spec.get("visibility", visibility),
                "auto_init": True,
                "has_issues": True,
                "has_projects": True,
                "has_wiki": False,
                "has_discussions": False,
                "delete_branch_on_merge": True,
                "allow_squash_merge": True,
                "allow_merge_commit": True,
                "allow_rebase_merge": True,
            },
        )
        if status != 201:
            raise RuntimeError(f"create {full_name} failed with HTTP {status}: {payload}")
        print(f"created: {full_name}")
    else:
        print(f"exists: {full_name}")
    configure_repo(token, full_name, spec)
    return full_name


def read_file(token: str, full_name: str, path: str) -> tuple[str, bytes] | None:
    status, payload = request(
        token,
        "GET",
        f"/repos/{full_name}/contents/{encoded(path)}?ref=main",
    )
    if status == 404:
        return None
    if status != 200 or payload.get("encoding") != "base64":
        raise RuntimeError(f"read {full_name}/{path} failed with HTTP {status}: {payload}")
    return payload["sha"], base64.b64decode(payload["content"].replace("\n", ""))


def put_file(token: str, full_name: str, path: str, content: bytes) -> None:
    present = read_file(token, full_name, path)
    if present is not None and present[1] == content:
        print(f"unchanged: {full_name}/{path}")
        return
    body: dict[str, Any] = {
        "message": f"Provision {path} from reviewed ores-otel template",
        "content": base64.b64encode(content).decode("ascii"),
        "branch": "main",
    }
    if present is not None:
        body["sha"] = present[0]
    status, payload = request(
        token,
        "PUT",
        f"/repos/{full_name}/contents/{encoded(path)}",
        body,
    )
    if status not in (200, 201):
        raise RuntimeError(f"write {full_name}/{path} failed with HTTP {status}: {payload}")
    print(f"seeded: {full_name}/{path}")


def delete_file(token: str, full_name: str, path: str) -> None:
    present = read_file(token, full_name, path)
    if present is None:
        return
    status, payload = request(
        token,
        "DELETE",
        f"/repos/{full_name}/contents/{encoded(path)}",
        {
            "message": f"Remove stale reviewed template path {path}",
            "sha": present[0],
            "branch": "main",
        },
    )
    if status != 200:
        raise RuntimeError(f"delete {full_name}/{path} failed with HTTP {status}: {payload}")
    print(f"removed stale template path: {full_name}/{path}")


def wait_for_main(token: str, full_name: str) -> None:
    for _ in range(30):
        status, _ = request(token, "GET", f"/repos/{full_name}/git/ref/heads/main")
        if status == 200:
            return
        if status != 404:
            raise RuntimeError(f"main branch readiness check failed for {full_name}: HTTP {status}")
        time.sleep(1)
    raise RuntimeError(f"main branch was not ready for {full_name}")


def template_files(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise RuntimeError(f"template directory missing: {root}")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"template symlink is forbidden: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    if not files:
        raise RuntimeError(f"template contains no files: {root}")
    return files


def load_previous_paths(token: str, full_name: str) -> set[str]:
    present = read_file(token, full_name, MANIFEST_PATH)
    if present is None:
        return set()
    try:
        document = json.loads(present[1])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid prior template manifest in {full_name}: {error}") from error
    if document.get("schema") != "ores.otel.repository-template/v1":
        raise RuntimeError(f"unrecognized prior template manifest in {full_name}")
    return set(document.get("files", {}))


def provision_one(token: str, manifest_root: Path, spec: dict[str, Any], visibility: str) -> None:
    full_name = ensure_repo(token, spec, visibility)
    wait_for_main(token, full_name)
    files = template_files((manifest_root / spec["template"]).resolve())
    previous = load_previous_paths(token, full_name)
    for stale in sorted(previous - set(files)):
        delete_file(token, full_name, stale)
    for path, content in files.items():
        put_file(token, full_name, path, content)
    provenance = {
        "schema": "ores.otel.repository-template/v1",
        "source": "ores-otel/.github",
        "template": spec["template"],
        "files": {
            path: hashlib.sha256(content).hexdigest()
            for path, content in sorted(files.items())
        },
    }
    put_file(
        token,
        full_name,
        MANIFEST_PATH,
        (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    for path, digest in provenance["files"].items():
        present = read_file(token, full_name, path)
        if present is None or hashlib.sha256(present[1]).hexdigest() != digest:
            raise RuntimeError(f"post-write verification failed: {full_name}/{path}")
    print(f"verified template: {full_name}; files={len(files)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--token-env", default="GH_ADMIN_TOKEN")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise RuntimeError(f"required token environment variable is empty: {args.token_env}")
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shared = manifest.get("sharedRepositories", [])
    if [spec.get("name") for spec in shared] != ["ores-interfaces", "ores-lib-core"]:
        raise RuntimeError("shared repository scope/order is not the reviewed pair")
    for spec in shared:
        provision_one(token, manifest_path.parent, spec, manifest["visibility"])
    print(f"shared repository fleet ready: repositories={len(shared)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
