#!/usr/bin/env python3
"""Validate a static Pages release archive before it is extracted or published."""

import os
import posixpath
import stat
import sys
import tarfile
from typing import NoReturn


MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_MEMBERS = 10_000
MAX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_PATH_BYTES = 4096


def fail(message: str) -> NoReturn:
    raise SystemExit(f"unsafe release archive: {message}")


def validate(archive: str) -> None:
    try:
        archive_size = os.stat(archive).st_size
    except OSError as error:
        fail(f"cannot stat archive: {error}")
    if archive_size <= 0 or archive_size > MAX_ARCHIVE_BYTES:
        fail("archive size limit exceeded")

    entries: dict[str, str] = {}
    total_bytes = 0
    try:
        source = tarfile.open(archive, mode="r:gz")
    except (OSError, tarfile.TarError) as error:
        fail(f"cannot read archive: {error}")

    with source:
        for member_number, member in enumerate(source, start=1):
            if member_number > MAX_MEMBERS:
                fail("member count limit exceeded")
            name = member.name
            if (
                not name
                or len(name.encode("utf-8", "surrogateescape")) > MAX_PATH_BYTES
                or "\x00" in name
                or any(ord(char) < 0x20 or ord(char) == 0x7F for char in name)
                or name.startswith("/")
            ):
                fail(f"invalid path {name!r}")
            parts = name.split("/")
            if ".." in parts:
                fail(f"path traversal {name!r}")
            canonical = "/".join(part for part in parts if part not in ("", ".")) or "."
            if canonical in entries:
                fail(f"duplicate path {name!r}")

            if member.isdir():
                kind = "directory"
            elif member.isreg():
                kind = "file"
                if member.size < 0 or member.size > MAX_UNCOMPRESSED_BYTES:
                    fail(f"invalid file size {name!r}")
                total_bytes += member.size
                if total_bytes > MAX_UNCOMPRESSED_BYTES:
                    fail("uncompressed size limit exceeded")
            elif member.issym() or member.islnk():
                fail(f"link entry {name!r}")
            elif member.ischr() or member.isblk() or member.isfifo() or stat.S_ISSOCK(member.mode):
                fail(f"special entry {name!r}")
            else:
                fail(f"unsupported entry type {name!r}")
            entries[canonical] = kind

    for path, kind in entries.items():
        if kind == "directory":
            continue
        if any(other.startswith(f"{path}/") for other in entries):
            fail(f"file conflicts with child path {path!r}")
        parent = posixpath.dirname(path)
        while parent and parent != ".":
            if entries.get(parent) not in (None, "directory"):
                fail(f"file conflicts with parent path {parent!r}")
            parent = posixpath.dirname(parent)

    if not entries:
        fail("archive has no members")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} ARCHIVE")
    validate(sys.argv[1])
