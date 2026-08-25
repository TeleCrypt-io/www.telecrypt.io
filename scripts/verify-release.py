"""Verify only the Release fields that bind the tested static artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

TAG = re.compile(r"www-v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
UTC_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
MAX_JSON_BYTES = 1024 * 1024
MAX_ASSET_BYTES = 100 * 1024 * 1024


class DuplicateJSONKey(ValueError):
    """Reject ambiguous object members at the metadata trust boundary."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(f"duplicate key {key!r}")
        result[key] = value
    return result


def fail(message: str) -> None:
    raise SystemExit(f"release metadata: {message}")


def bounded(path: Path, limit: int) -> bytes:
    try:
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
    except OSError as error:
        fail(f"cannot read {path}: {error}")
    if len(data) > limit:
        fail(f"{path} exceeds its byte limit")
    return data


def positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        fail(f"{label} is not a positive integer")
    return value


def timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        fail(f"{label} is not an exact UTC timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        fail(f"{label} is invalid: {error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--expected-target-commit", required=True)
    parser.add_argument("--state", choices=("draft", "published"), required=True)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--max-asset-bytes", type=int, default=MAX_ASSET_BYTES)
    parser.add_argument("--expected-release-id", type=int)
    args = parser.parse_args()
    if not TAG.fullmatch(args.tag):
        fail("tag is not an exact www semver tag")
    if args.asset_name != f"{args.tag}.tar.gz":
        fail("asset name is not exact")
    if not 0 < args.max_asset_bytes <= MAX_ASSET_BYTES:
        fail("asset limit is invalid")
    try:
        release = json.loads(
            bounded(args.json, MAX_JSON_BYTES).decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJSONKey) as error:
        fail(f"Release JSON is invalid: {error}")
    if not isinstance(release, dict):
        fail("Release JSON is not an object")
    release_id = positive(release.get("id"), "Release id")
    if args.expected_release_id is not None and release_id != positive(args.expected_release_id, "expected Release id"):
        fail("Release id changed during recovery")
    expected_draft = args.state == "draft"
    immutable_ok = release.get("immutable") is True if not expected_draft else release.get("immutable") in (False, None)
    created_at = timestamp(release.get("created_at"), "created_at")
    published_at = release.get("published_at")
    if expected_draft:
        if published_at is not None:
            fail("draft Release must not have published_at")
    else:
        published_at = timestamp(published_at, "published_at")
        if published_at < created_at:
            fail("published_at precedes created_at")
    if (
        release.get("tag_name") != args.tag
        or release.get("name") != args.tag
        or release.get("body") != f"Release {args.tag}"
        or release.get("target_commitish") != args.expected_target_commit
        or release.get("draft") is not expected_draft
        or release.get("prerelease") is not False
        or not immutable_ok
    ):
        fail("Release tag, name, state, or immutable flag is not exact")
    assets = release.get("assets")
    if not isinstance(assets, list) or len(assets) != 1 or not isinstance(assets[0], dict):
        fail("Release asset count is not exactly one")
    asset = assets[0]
    if asset.get("name") != args.asset_name or asset.get("state") != "uploaded":
        fail("Release asset name or state is not exact")
    asset_id = positive(asset.get("id"), "asset id")
    size = positive(asset.get("size"), "asset size")
    if size > args.max_asset_bytes:
        fail("Release asset exceeds its byte limit")
    digest = asset.get("digest")
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        fail("Release asset digest is not exact")
    if args.artifact is not None:
        data = bounded(args.artifact, args.max_asset_bytes)
        if len(data) != size or f"sha256:{hashlib.sha256(data).hexdigest()}" != digest:
            fail("downloaded bytes do not match Release metadata")
    print(json.dumps({"asset_id": asset_id, "digest": digest, "release_id": release_id, "size": size}, sort_keys=True))


if __name__ == "__main__":
    main()
