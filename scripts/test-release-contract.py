"""Offline behavioral checks for the www immutable Release contract."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
VERIFY_SOURCE = (ROOT / "scripts/verify-source.sh").read_text(encoding="utf-8")
FOOTER = (ROOT / "src/components/layout/Footer.astro").read_text(encoding="utf-8")
BASE_HEAD = (ROOT / "src/components/BaseHead.astro").read_text(encoding="utf-8")
PRIVACY_PAGE = (ROOT / "src/pages/privacy.astro").read_text(encoding="utf-8")
PRIVACY_TEXT = (ROOT / "src/pages/privacy.txt.ts").read_text(encoding="utf-8")
ROBOTS = (ROOT / "src/pages/robots.txt.ts").read_text(encoding="utf-8")
INDEX_PAGE = (ROOT / "src/pages/index.astro").read_text(encoding="utf-8")
SITE_CONFIG = (ROOT / "src/site.config.ts").read_text(encoding="utf-8")
ASTRO_CONFIG = (ROOT / "astro.config.ts").read_text(encoding="utf-8")
LLMS_PAGE = (ROOT / "src/pages/llms.astro").read_text(encoding="utf-8")
ABOUT_TEXT = (ROOT / "src/content/page/about.md").read_text(encoding="utf-8")
README_TEXT = (ROOT / "README.md").read_text(encoding="utf-8")


class ContractError(AssertionError):
    pass


def check_source_verification() -> None:
    if "|| true" in VERIFY_SOURCE:
        raise ContractError("source verification discards a required Git cleanup result")
    for fragment in (
        'if test "$config_status" = 0; then',
        'sort -u -- "$config_file" >"$config_file.unique"',
        'git config --local --no-includes --unset-all "$key"',
        'elif test "$config_status" != 1; then',
        'timeout --signal=TERM --kill-after=5s 60s',
    ):
        if fragment not in VERIFY_SOURCE:
            raise ContractError(f"source verification is missing {fragment}")


def exact_published(tag: str) -> dict:
    return {
        "id": 42,
        "tag_name": tag,
        "name": tag,
        "body": f"Release {tag}",
        "target_commitish": "a" * 40,
        "created_at": "2026-08-24T00:00:00Z",
        "published_at": "2026-08-24T00:00:01Z",
        "draft": False,
        "prerelease": False,
        "immutable": True,
        "assets": [{"id": 43, "name": f"{tag}.tar.gz", "state": "uploaded", "size": 10, "digest": f"sha256:{'a' * 64}"}],
    }


def exact_draft(tag: str) -> dict:
    return {
        "id": 42,
        "tag_name": tag,
        "name": tag,
        "body": f"Release {tag}",
        "target_commitish": "a" * 40,
        "created_at": "2026-08-24T00:00:00Z",
        "published_at": None,
        "draft": True,
        "prerelease": False,
        "immutable": False,
        "assets": [],
    }


def require_exact_draft(probe: dict) -> None:
    if (
        not isinstance(probe.get("id"), int)
        or isinstance(probe.get("id"), bool)
        or probe["id"] <= 0
        or not isinstance(probe.get("created_at"), str)
        or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", probe["created_at"]) is None
        or probe.get("published_at") is not None
        or probe.get("immutable") not in (False, None)
        or not isinstance(probe.get("assets"), list)
        or any(
            not isinstance(asset, dict)
            or not isinstance(asset.get("id"), int)
            or isinstance(asset.get("id"), bool)
            or asset["id"] <= 0
            for asset in probe["assets"]
        )
    ):
        raise ContractError("draft Release metadata or assets are not exact")


def publication_action(probe: dict | None, attempt: int, tag: str = "www-v1.2.3") -> str:
    if probe is None:
        return "create-draft"
    if probe.get("transport") in {"timeout", "error"}:
        raise ContractError("transport failure is not a confirmed 404")
    if probe.get("tag_name") != tag or probe.get("name") != tag or probe.get("body") != f"Release {tag}" or probe.get("prerelease") is not False:
        raise ContractError("Release identity conflict")
    if probe.get("draft") is True:
        require_exact_draft(probe)
        return "reuse-draft"
    if probe.get("draft") is False:
        if attempt <= 1 or probe.get("immutable") is not True or probe.get("assets") != exact_published(tag)["assets"]:
            raise ContractError("published Release is not an exact rerun state")
        return "reuse-published"
    raise ContractError("unknown Release state")


def final_publish_recheck(probe: dict, tag: str = "www-v1.2.3") -> None:
    """Model the final remote read that must precede the draft->published PATCH."""
    publication_action(probe, 1, tag)
    assets = probe.get("assets")
    if probe.get("id") != 42 or not isinstance(assets, list) or len(assets) != 1 or assets[0].get("id") != 43 or assets[0].get("name") != f"{tag}.tar.gz" or assets[0].get("state") != "uploaded" or assets[0].get("size") != 10 or assets[0].get("digest") != f"sha256:{'a' * 64}":
        raise ContractError("final draft artifact changed")


def discover_release_id(pages: list[object], tag: str) -> int | None:
    """Model bounded pagination and the unique positive numeric-ID selection."""
    if not pages:
        raise ContractError("Release list is incomplete")
    matches: list[int] = []
    for page_number, page in enumerate(pages):
        if not isinstance(page, list) or len(page) > 100 or any(not isinstance(release, dict) for release in page):
            raise ContractError("Release page is not a complete bounded object array")
        if len(page) < 100 and page_number != len(pages) - 1:
            raise ContractError("Release list continued after its terminal page")
        for release in page:
            release_id = release.get("id")
            if isinstance(release_id, bool) or not isinstance(release_id, int) or release_id <= 0 or not isinstance(release.get("tag_name"), str):
                raise ContractError("Release page contains an invalid compact record")
            if release.get("tag_name") == tag:
                matches.append(release_id)
    if len(pages[-1]) == 100:
        raise ContractError("Release list is incomplete")
    if len(matches) > 1:
        raise ContractError("multiple Releases match the release tag")
    return matches[0] if matches else None


def check_state_machine() -> None:
    tag = "www-v1.2.3"
    assert publication_action(None, 1, tag) == "create-draft"
    assert publication_action(exact_draft(tag), 1, tag) == "reuse-draft"
    assert publication_action(exact_published(tag), 2, tag) == "reuse-published"
    final_draft = {**exact_draft(tag), "assets": [{"id": 43, "name": f"{tag}.tar.gz", "state": "uploaded", "size": 10, "digest": f"sha256:{'a' * 64}"}]}
    final_publish_recheck(final_draft, tag)
    for field in (
        "id", "tag_name", "name", "body", "draft", "prerelease", "immutable",
        "created_at", "published_at", "asset_state", "asset_size", "assets", "asset_id", "duplicate_name",
        "duplicate_id",
    ):
        mutated = {**final_draft}
        if field == "assets":
            mutated["assets"] = [{**final_draft["assets"][0], "digest": f"sha256:{'b' * 64}"}]
        elif field == "asset_id":
            mutated["assets"] = [{**final_draft["assets"][0], "id": 44}]
        elif field == "duplicate_name":
            mutated["assets"] = [final_draft["assets"][0], {**final_draft["assets"][0], "id": 44}]
        elif field == "duplicate_id":
            mutated["assets"] = [final_draft["assets"][0], {**final_draft["assets"][0], "name": "other.tar.gz"}]
        elif field == "asset_state":
            mutated["assets"] = [{**final_draft["assets"][0], "state": "pending"}]
        elif field == "asset_size":
            mutated["assets"] = [{**final_draft["assets"][0], "size": 11}]
        elif field == "id":
            mutated["id"] = 43
        elif field == "immutable":
            mutated["immutable"] = True
        elif field == "created_at":
            mutated["created_at"] = "not-a-timestamp"
        elif field == "published_at":
            mutated["published_at"] = "2026-08-24T00:00:01Z"
        else:
            mutated[field] = False if field == "draft" else True if field == "prerelease" else "changed"
        try:
            final_publish_recheck(mutated, tag)
        except ContractError:
            continue
        raise ContractError(f"final draft recheck accepted a {field} mutation")
    for invalid in (
        {"transport": "timeout"},
        {"transport": "error"},
        {**exact_published(tag), "assets": []},
        {**exact_published(tag), "immutable": False},
        {**exact_draft(tag), "published_at": "2026-08-24T00:00:01Z"},
        {**exact_draft(tag), "id": 0},
        {**exact_draft(tag), "assets": [{"id": 0}]},
        {**exact_draft(tag), "created_at": "not-a-timestamp"},
    ):
        try:
            publication_action(invalid, 2, tag)
        except ContractError:
            continue
        raise ContractError("invalid remote state was accepted")
    try:
        publication_action(exact_published(tag), 1, tag)
    except ContractError:
        pass
    else:
        raise ContractError("published Release was accepted on the initial attempt")
    full_page = [{"id": release_id, "tag_name": f"other-{release_id}"} for release_id in range(1, 101)]
    assert discover_release_id([full_page, [{"id": 101, "tag_name": tag}]], tag) == 101
    assert discover_release_id([[{"id": 42, "tag_name": tag}]], tag) == 42
    assert discover_release_id([[]], tag) is None
    for invalid_pages in (
        [[exact_draft(tag)], [exact_draft(tag)]],
        [full_page],
        [{"not": "a page"}],
        [list(range(101))],
        [[{**exact_draft(tag), "id": 0}]],
        [[{**exact_draft(tag), "id": True}]],
        [[{"id": 0, "tag_name": "other"}]],
        [[{"id": 42}]],
    ):
        try:
            discover_release_id(invalid_pages, tag)
        except ContractError:
            continue
        raise ContractError("incomplete or ambiguous Release-list state was accepted")


def check_site_contract() -> None:
    # This is deliberately structural and offline. The generated-link validator runs in the
    # release workflow after Astro builds; this contract test must not build the application.
    if not re.search(
        r"(?m)^\s*export\s+const\s+siteUrl\s*=\s*(['\"])https://www\.telecrypt\.io\1\s*;",
        SITE_CONFIG,
    ):
        raise ContractError("site URL is not an explicit production constant")
    authority_url = "https://telecrypt.io/llms.txt"
    if not re.search(rf"(?m)^\s*export\s+const\s+llmsAuthorityUrl\s*=\s*(['\"])" + re.escape(authority_url) + r"\1\s*;", SITE_CONFIG):
        raise ContractError("llms authority URL is not an explicit Pages constant")
    forbidden_authority_sources = (
        ROOT / "public/llms.txt",
        ROOT / "src/content/llms.txt",
        ROOT / "src/pages/llms.txt.ts",
        ROOT / "src/pages/llms.txt.astro",
    )
    if any(path.exists() for path in forbidden_authority_sources):
        raise ContractError("website retains an embedded llms.txt source or route")
    if "llmsAuthorityUrl" not in LLMS_PAGE or "llmsAuthorityUrl" not in FOOTER or "llmsAuthorityUrl" not in INDEX_PAGE:
        raise ContractError("site's rendered llms links do not use the canonical authority constant")
    if authority_url not in ABOUT_TEXT or authority_url not in README_TEXT:
        raise ContractError("site's llms links do not target the canonical Pages authority")
    if not re.search(r"(?m)^\s*site\s*:\s*siteUrl\s*,", ASTRO_CONFIG):
        raise ContractError("Astro is not bound to the production site constant")
    if any(marker in SITE_CONFIG or marker in ASTRO_CONFIG for marker in ("SERVER_NAME", "PUBLIC_SITE", "import.meta.env", "process.env")):
        raise ContractError("site host has an ambient or environment-derived input")
    home_title = re.search(
        r"(?ms)^\s*const\s+meta\s*=\s*\{\s*title\s*:\s*(['\"])(?P<title>[^'\"]+)\1\s*,",
        INDEX_PAGE,
    )
    if home_title is None or home_title.group("title") == "TeleCrypt.io":
        raise ContractError("home page title duplicates the canonical brand")

    if not re.search(
        r"const\s+canonicalURL\s*=\s*new\s+URL\(\s*Astro\.url\.pathname\s*,\s*Astro\.site\s*\)",
        BASE_HEAD,
    ):
        raise ContractError("canonical URL is not derived from the configured Astro site")

    def has_element(tag: str, attributes: dict[str, str]) -> bool:
        lookaheads = "".join(
            rf"(?=[^>]*\b{re.escape(name)}\s*=\s*{value})"
            for name, value in attributes.items()
        )
        return re.search(rf"<{tag}\b{lookaheads}[^>]*>", BASE_HEAD, re.DOTALL) is not None

    astro_expression = r"\{\s*canonicalURL\s*\}"
    for label, attributes in (
        ("canonical link", {"href": astro_expression, "rel": r"['\"]canonical['\"]"}),
        ("OpenGraph URL", {"content": astro_expression, "property": r"['\"]og:url['\"]"}),
        ("Twitter URL", {"content": astro_expression, "name": r"['\"]twitter:url['\"]"}),
        ("sitemap link", {"href": r"['\"]/sitemap-index\.xml['\"]", "rel": r"['\"]sitemap['\"]"}),
    ):
        if not has_element("link" if label.endswith("link") else "meta", attributes):
            raise ContractError(f"{label} is not bound to the canonical site wiring")
    if not re.search(
        r"const\s+socialImageURL\s*=\s*new\s+URL\(\s*['\"]/social-card\.png['\"]\s*,\s*Astro\.site\s*\)",
        BASE_HEAD,
    ):
        raise ContractError("social image URL is not derived from the configured Astro site")

    if not re.search(r"loadPage\(\s*['\"]privacy['\"]", PRIVACY_PAGE):
        raise ContractError("privacy HTML page is not loaded from the privacy content entry")
    if not re.search(r"getEntry\(\s*['\"]page['\"]\s*,\s*['\"]privacy['\"]\s*\)", PRIVACY_TEXT):
        raise ContractError("privacy text route is not loaded from the privacy content entry")
    if not re.search(r"new\s+Response\(\s*entry\.body\b", PRIVACY_TEXT):
        raise ContractError("privacy text route does not expose the shared content body")
    if not re.search(r"<a\b[^>]*\bhref\s*=\s*['\"]/privacy/['\"][^>]*>", FOOTER):
        raise ContractError("site navigation does not link to the privacy page")

    if not re.search(
        r"new\s+URL\(\s*['\"]sitemap-index\.xml['\"]\s*,\s*site\s*\)",
        ROBOTS,
    ) or not re.search(r"Sitemap:\s*\$\{sitemapURL\.href\}", ROBOTS):
        raise ContractError("robots sitemap is not derived from the configured Astro site")


check_source_verification()
check_state_machine()
check_site_contract()
print("www Release behavioral invariants passed")
