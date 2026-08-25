"""Offline behavioral checks for the www immutable Release contract."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
VERIFY = (ROOT / ".github/workflows/verify.yml").read_text(encoding="utf-8")
VERIFIER = (ROOT / "scripts/verify-release.py").read_text(encoding="utf-8")
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
PACKAGE = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))


class ContractError(AssertionError):
    pass


def job(name: str) -> str:
    match = re.search(rf"^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:|\Z)", WORKFLOW, re.MULTILINE | re.DOTALL)
    if not match:
        raise ContractError(f"missing workflow job: {name}")
    return match.group("body")


def step(job_text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = job_text.find(marker)
    if start < 0:
        raise ContractError(f"missing step: {name}")
    shell = job_text.find("        run: |\n", start)
    if shell < 0:
        raise ContractError(f"step has no shell: {name}")
    body_start = shell + len("        run: |\n")
    end = job_text.find("\n      - ", body_start)
    return job_text[body_start:] if end < 0 else job_text[body_start:end]


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
        or len(probe["assets"]) > 64
        or any(
            not isinstance(asset, dict)
            or not isinstance(asset.get("id"), int)
            or isinstance(asset.get("id"), bool)
            or asset["id"] <= 0
            for asset in probe["assets"]
        )
    ):
        raise ContractError("draft Release metadata or assets are not bounded and exact")


def publication_action(probe: dict | None, attempt: int, tag: str = "www-v1.2.3") -> str:
    if probe is None:
        return "create-draft"
    if probe.get("transport") in {"timeout", "error"}:
        raise ContractError("transport failure is not a confirmed 404")
    if probe.get("tag_name") != tag or probe.get("name") != tag or probe.get("body") != f"Release {tag}" or probe.get("target_commitish") != "a" * 40 or probe.get("prerelease") is not False:
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


def check_state_machine() -> None:
    tag = "www-v1.2.3"
    assert publication_action(None, 1, tag) == "create-draft"
    assert publication_action(exact_draft(tag), 1, tag) == "reuse-draft"
    assert publication_action(exact_published(tag), 2, tag) == "reuse-published"
    final_draft = {**exact_draft(tag), "assets": [{"id": 43, "name": f"{tag}.tar.gz", "state": "uploaded", "size": 10, "digest": f"sha256:{'a' * 64}"}]}
    final_publish_recheck(final_draft, tag)
    for field in (
        "id", "tag_name", "name", "body", "target_commitish", "draft", "prerelease", "immutable",
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


def check_workflow() -> None:
    if (ROOT / ".nvmrc").exists():
        raise ContractError("obsolete .nvmrc Node.js declaration remains")
    if (ROOT / ".node-version").read_text(encoding="utf-8").strip() != "22.23.2" or PACKAGE.get("engines", {}).get("node") != "22.23.2":
        raise ContractError("Node.js version is not declared exactly")
    if "test \"$(node --version)\" = v22.23.2" not in WORKFLOW or "test \"$(pnpm --version)\" = 11.22.0" not in WORKFLOW:
        raise ContractError("workflow does not verify the exact Node.js and pnpm toolchain")
    if "PUBLIC_RELEASE_YEAR" in FOOTER or "import.meta.env" in FOOTER:
        raise ContractError("Footer has an ambient release-year build input")
    release_shell = step(job("release"), "Create or reuse the exact draft Release")
    for fragment in (
        "refs/tags/$RELEASE_TAG:refs/remotes/origin/release-tag", "refs/heads/main:refs/remotes/origin/main",
        "git cat-file -t refs/remotes/origin/release-tag", "git merge-base --is-ancestor",
        "https://github.com/${GITHUB_REPOSITORY}.git", "--no-includes", "protocol.file.allow=never",
        "protocol.ext.allow=never", "protocol.ssh.allow=never", "credential.helper=", "core.askPass=/bin/false",
        "http.proxy=", "https.proxy=", "scripts/bounded-command.py", "--include", "status_line", "--method POST",
        "--field draft=true", "--method DELETE", "--input \"$archive\"", "Accept: application/octet-stream",
        "cmp -s \"$archive\"", "--method PATCH", "--field draft=false", "GITHUB_RUN_ATTEMPT",
        "verify-release.py", "validate-pages-artifact.py", "--expected-target-commit", "target_commitish", "created_at", "published_at",
    ):
        if fragment not in release_shell:
            raise ContractError(f"release state machine is missing {fragment}")
    if "github.run_attempt" in WORKFLOW:
        raise ContractError("artifact names vary across reruns")
    if "name: www-release-${{ github.run_id }}-${{ github.sha }}" not in WORKFLOW or "overwrite: true" not in WORKFLOW:
        raise ContractError("website artifact reruns are not stable and overwritable")
    if "--output" in WORKFLOW:
        raise ContractError("binary downloads still use unsupported gh api --output")
    if "upload_url" not in release_shell or "uploads.github.com" not in release_shell or '"$upload_url?name=$asset_name"' not in release_shell:
        raise ContractError("Release asset upload does not use the authoritative uploads.github.com URL")
    if release_shell.index("--method POST") > release_shell.index("--method DELETE") or release_shell.index("--method DELETE") > release_shell.index("--input \"$archive\"") or release_shell.index("--input \"$archive\"") > release_shell.index("--method PATCH"):
        raise ContractError("draft lifecycle operations are out of order")
    for fragment in ("GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_NO_REPLACE_OBJECTS", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_ALLOW_PROTOCOL", "GH_HOST: github.com", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        if fragment not in WORKFLOW:
            raise ContractError(f"transport hardening is missing {fragment}")
    if "gh release create" in WORKFLOW or "release create" in WORKFLOW or "--draft" in WORKFLOW or "releases?per_page=" in WORKFLOW:
        raise ContractError("one-shot or broad Release recovery remains")
    if WORKFLOW.count("release:\n    needs: build") != 1 or "promote:\n    needs: [build, release]" not in WORKFLOW:
        raise ContractError("publication/deployment dependencies are not explicit")
    if WORKFLOW.index("actions/upload-pages-artifact@v5.0.0") > WORKFLOW.index("actions/deploy-pages@v5.0.0"):
        raise ContractError("Pages deployment precedes artifact upload")
    if "immutable" not in VERIFIER or "digest" not in VERIFIER:
        raise ContractError("Release verifier does not bind immutable bytes")
    if "Run offline release helper" in VERIFY or "test-release-contract.py" not in VERIFY:
        raise ContractError("verification workflow is not using the behavioral contract")
    if "revalidate_draft_for_publish" not in release_shell:
        raise ContractError("the draft is not re-fetched immediately before publication")
    for fragment in ('if test "$status" -ne 0; then', 'cat -- "$output" >&2', 'cat -- "$error" >&2', 'if test -s "$error"; then', "grep -Eqv '^\\$ [[:print:]]*$'"):
        if fragment not in job("build"):
            raise ContractError(f"bounded build command does not preserve failure diagnostics: {fragment}")
    final_recheck = 'verify_source\n              revalidate_draft_for_publish "$probe" "$release_id"\n              bounded_gh "$RUNNER_TEMP/published.json"'
    if final_recheck not in release_shell:
        raise ContractError("publication does not perform the final source and Release recheck immediately before PATCH")


def check_site_contract() -> None:
    # This is deliberately structural and offline. The generated-link validator runs in the
    # release workflow after Astro builds; this contract test must not build the application.
    if not re.search(
        r"(?m)^\s*export\s+const\s+siteUrl\s*=\s*(['\"])https://www\.telecrypt\.io\1\s*;",
        SITE_CONFIG,
    ):
        raise ContractError("site URL is not an explicit production constant")
    authority_url = "https://telecrypt-io.github.io/llms-authority/llms.txt"
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


check_state_machine()
check_workflow()
check_site_contract()
print("www Release behavioral invariants passed")
