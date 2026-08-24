# TeleCrypt.io — landing

Static landing site for **TeleCrypt.io**, published at
`https://www.telecrypt.io/` through GitHub Pages.

This repository is production-only. Its public host is fixed at `www.telecrypt.io`; it has no
environment or server-name input and does not support `www.<SERVER_NAME>` preproduction variants.

> Secure transport for agents and human beings.

Built with [Astro](https://astro.build) and published as a fully static build.

## Content

The site contains the landing page, pricing, technology, About, support, privacy, and export pages.
The canonical machine-readable `llms.txt` is maintained in
[`llms-authority`](https://github.com/TeleCrypt-io/llms-authority) and served from its GitHub Pages
URL. This site links to that authority rather than copying it. `export.txt` is served verbatim, and
`privacy.txt` is generated from the same source as the privacy page.

## Develop

Use Node.js 22.23.2 and pnpm 11.22.0, as declared by `.node-version` and `package.json`.

```sh
pnpm install --frozen-lockfile
pnpm run check
pnpm run lint
pnpm run dev      # http://localhost:4321
```

## Deploy

This repo holds **source only**; `dist/` is gitignored. Pushes and pull requests to `main` only
verify the source. An exact annotated `www-v*` tag is tested and built once, then published with its
deterministic static artifact as an immutable GitHub Release. The same workflow promotes that
verified release artifact to GitHub Pages without rebuilding, so every deployment identifies its
exact source release rather than a branch. Configure
the repository's Pages custom domain as `www.telecrypt.io`. The site URL is a committed production
constant, not a deployment-time setting.

These public workflows verify and publish the static artifact; acceptance of the deployed site is
operator-managed outside this repository.

The repository's immutable-Releases setting and a protected, non-force-movable `www-v*` tag
ruleset are operator/Harness pre-tag prerequisites. The Actions token cannot read the administration
endpoints, so Harness must block tag publication unless both settings have been verified. The
release and Pages workflows fail closed if the final Release is not exact, non-prerelease, and
immutable; they compare the archive with the Release API's SHA-256 asset digest rather than
publishing a separate checksum asset. The tested archive is transferred under a
run/attempt/commit-specific artifact name and its size and digest are checked again before Release
creation and Pages promotion. If a runner interruption leaves an already published immutable
Release, a rerun accepts it only after the body, Release and asset IDs, timestamps, source
annotated-tag SHA, metadata, and exact bytes match. A rerun can also recover an exact draft through
the tag-specific Release endpoint, then verifies the full draft and downloaded bytes before
publishing it; a missing tag creates a new draft only after a confirmed 404, and mismatches remain
fail-closed for manual cleanup. The workflow does not scan a broad Releases list. Release creation,
asset upload, and publication are separate remote operations,
so the workflow does not claim atomicity across an interruption or a tag mutation race. The hosted
artifact transfer action has no supported pre-write byte-limit option; the producer and immediate
consumer enforce the run-specific size/digest binding and reject any oversized or mismatched
transfer before Release or Pages use.

The apex domain, `telecrypt.io`, is intentionally separate: it provides Matrix discovery and
redirects browser traffic to `www.telecrypt.io`. Matrix client, authentication, and control-plane
APIs are served at `https://backend.telecrypt.io`; Matrix IDs remain `@user:telecrypt.io`.

## License

This inherited Astro Sienna site is licensed under [MIT](./LICENSE). The other TeleCrypt source
repositories use BUSL-1.1; this repository remains the documented exception.
