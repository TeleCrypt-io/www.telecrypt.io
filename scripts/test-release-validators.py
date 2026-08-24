#!/usr/bin/env python3
"""Adversarial offline fixtures for the www release trust-boundary validators."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_VALIDATOR = ROOT / "scripts/validate-pages-artifact.py"
RELEASE_VALIDATOR = ROOT / "scripts/verify-release.py"
TAG = "www-v1.2.3"


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd or ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def make_tar(path: Path, members: list[tarfile.TarInfo | tuple[str, bytes]]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for member in members:
            if isinstance(member, tuple):
                name, data = member
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            else:
                archive.addfile(member)


class PagesArchiveFixtures(unittest.TestCase):
    def check_archive(self, members: list[tarfile.TarInfo | tuple[str, bytes]], valid: bool) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "site.tar.gz"
            make_tar(archive, members)
            result = run([sys.executable, str(ARCHIVE_VALIDATOR), str(archive)])
            if valid:
                self.assertEqual(result.returncode, 0, result.stderr)
            else:
                self.assertNotEqual(result.returncode, 0)

    def test_accepts_regular_members(self) -> None:
        self.check_archive([("index.html", b"ok"), ("CNAME", b"www.telecrypt.io\n")], True)

    def test_rejects_traversal_absolute_duplicate_and_conflict(self) -> None:
        baseline = [("index.html", b"ok"), ("CNAME", b"www.telecrypt.io\n")]
        for extra in ("../escape", "/absolute", "assets", "assets/app.js"):
            members = baseline + [(extra, b"x")]
            if extra == "assets":
                members.append(("assets/app.js", b"x"))
            if extra == "assets/app.js":
                members.append(("assets/app.js", b"duplicate"))
            self.check_archive(members, False)

    def test_rejects_links_and_special_files(self) -> None:
        link = tarfile.TarInfo("link")
        link.type = tarfile.SYMTYPE
        link.linkname = "index.html"
        fifo = tarfile.TarInfo("pipe")
        fifo.type = tarfile.FIFOTYPE
        self.check_archive([("index.html", b"ok"), link], False)
        self.check_archive([("index.html", b"ok"), fifo], False)


class ReleaseMetadataFixtures(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifact = self.root / f"{TAG}.tar.gz"
        self.artifact.write_bytes(b"immutable tested bytes")
        digest = f"sha256:{hashlib.sha256(self.artifact.read_bytes()).hexdigest()}"
        self.metadata = {
            "id": 42,
            "tag_name": TAG,
            "name": TAG,
            "body": f"Release {TAG}",
            "target_commitish": "a" * 40,
            "created_at": "2026-08-24T00:00:00Z",
            "published_at": "2026-08-24T00:00:01Z",
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "assets": [{"id": 99, "name": f"{TAG}.tar.gz", "state": "uploaded", "size": self.artifact.stat().st_size, "digest": digest}],
        }
        self.json_path = self.root / "release.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def check(self, metadata: dict, artifact: Path | None = None, expected_id: int | None = 42, state: str = "published") -> subprocess.CompletedProcess[str]:
        self.json_path.write_text(json.dumps(metadata), encoding="utf-8")
        command = [
            sys.executable,
            str(RELEASE_VALIDATOR),
            "--json",
            str(self.json_path),
            "--tag",
            TAG,
            "--asset-name",
            f"{TAG}.tar.gz",
            "--expected-target-commit",
            "a" * 40,
            "--state",
            state,
            "--max-asset-bytes",
            "1000",
        ]
        if artifact is not None:
            command += ["--artifact", str(artifact)]
        if expected_id is not None:
            command += ["--expected-release-id", str(expected_id)]
        return run(command)

    def test_accepts_exact_published_release_and_bytes(self) -> None:
        result = self.check(self.metadata, self.artifact)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["asset_id"], 99)

    def test_accepts_exact_draft_release_and_rejects_published_timestamp(self) -> None:
        draft = {**self.metadata, "draft": True, "immutable": False, "published_at": None}
        result = self.check(draft, self.artifact, state="draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        invalid = {**draft, "published_at": "2026-08-24T00:00:01Z"}
        self.assertNotEqual(self.check(invalid, self.artifact, state="draft").returncode, 0)

    def test_rejects_unimmutable_wrong_shape_and_wrong_bytes(self) -> None:
        for change in (
            {"immutable": False},
            {"assets": []},
            {"assets": [self.metadata["assets"][0], {"id": 100}]},
            {"draft": True},
            {"body": "tampered"},
            {"target_commitish": "main"},
            {"published_at": "2025-01-01T00:00:00Z"},
        ):
            metadata = {**self.metadata, **change}
            self.assertNotEqual(self.check(metadata).returncode, 0)
        wrong = self.root / "wrong.tar.gz"
        wrong.write_bytes(b"tampered bytes")
        self.assertNotEqual(self.check(self.metadata, wrong).returncode, 0)
        self.assertNotEqual(self.check(self.metadata, expected_id=43).returncode, 0)


if __name__ == "__main__":
    unittest.main()
