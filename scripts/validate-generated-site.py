#!/usr/bin/env python3
"""Validate the exact generated route and metadata set used by Pages."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


REQUIRED_FILES = (
    "404.html",
    "privacy.txt",
    "robots.txt",
    "sitemap-index.xml",
    "sitemap-0.xml",
    "CNAME",
    "export/index.html",
    "export.txt",
)
REQUIRED_ROUTES = (
    "index.html",
    "about/index.html",
    "price/index.html",
    "privacy/index.html",
    "support/index.html",
    "technology/index.html",
    "llms/index.html",
)
MAX_FILES = 10_000
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024


def fail(message: str) -> None:
    raise SystemExit(f"generated site: {message}")


def require_file(root: Path, relative: str) -> None:
    path = root / relative
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"required non-empty file is missing: {relative}")


def validate(root: Path) -> None:
    if not root.is_dir():
        fail(f"site root is not a directory: {root}")
    file_count = 0
    total_bytes = 0
    for directory, directories, files in os.walk(root, topdown=True, followlinks=False):
        for name in directories:
            if (Path(directory) / name).is_symlink():
                fail("generated site contains a symlink directory")
        for name in files:
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                fail(f"generated site contains a non-regular file: {path.relative_to(root)}")
            file_count += 1
            if file_count > MAX_FILES:
                fail("generated site file-count limit exceeded")
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                fail(f"generated site member-size limit exceeded: {path.relative_to(root)}")
            total_bytes += size
            if total_bytes > MAX_TOTAL_BYTES:
                fail("generated site aggregate-size limit exceeded")
            with path.open("rb") as stream:
                carry = b""
                while chunk := stream.read(1024 * 1024):
                    data = carry + chunk
                    if b"PUBLIC_RELEASE_YEAR" in data:
                        fail("generated site depends on PUBLIC_RELEASE_YEAR")
                    carry = data[-len(b"PUBLIC_RELEASE_YEAR") + 1 :]
    for route in REQUIRED_ROUTES:
        require_file(root, route)
    for relative in REQUIRED_FILES:
        require_file(root, relative)
    if (root / "llms.txt").exists():
        fail("generated site must not embed a second llms.txt authority")
    robots_lines = (root / "robots.txt").read_text(encoding="utf-8").splitlines()
    if "Sitemap: https://www.telecrypt.io/sitemap-index.xml" not in robots_lines:
        fail("robots.txt does not contain the canonical sitemap line")
    if (root / "CNAME").read_text(encoding="utf-8").strip() != "www.telecrypt.io":
        fail("CNAME is not www.telecrypt.io")
    if (root / "eject/index.html").exists() or (root / "eject.txt").exists():
        fail("eject route must not be generated")
    about_html = (root / "about/index.html").read_text(encoding="utf-8")
    if not about_html.lstrip().lower().startswith("<!doctype html>"):
        fail("about page must begin with a doctype")
    schema_marker = 'type="application/ld+json"'
    if about_html.count(schema_marker) != 1:
        fail("about page must contain exactly one JSON-LD document")
    head_start = about_html.find("<head")
    head_end = about_html.find("</head>")
    schema = about_html.find(schema_marker)
    if head_start < 0 or head_end < 0 or not head_start < schema < head_end:
        fail("about JSON-LD must be inside the document head")
    if '"@type":"AboutPage"' not in about_html or '"@type":"Organization"' not in about_html:
        fail("about JSON-LD is missing its page or organization type")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    validate(parser.parse_args().root)
