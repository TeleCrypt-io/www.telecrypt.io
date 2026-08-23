# TeleCrypt.io — landing

Static landing site for **TeleCrypt.io**, published at
`https://www.telecrypt.io/` through GitHub Pages.

> Secure transport for agents and human beings.

Built with [Astro](https://astro.build) and published as a fully static build.

## Content

The site contains the landing page, pricing, technology, About, support, privacy, and eject pages.
The machine-readable `llms.txt` is generated from its text template and the canonical plan facts,
`eject.txt` is served verbatim, and `privacy.txt` is generated from the same source as the privacy
page.

## Develop

```sh
pnpm install --frozen-lockfile
pnpm run check
pnpm run lint
pnpm run dev      # http://localhost:4321
```

## Deploy

This repo holds **source only**; `dist/` is gitignored. Pushes and pull requests to `main` only
verify the source. GitHub Pages builds and deploys only when an immutable `www-v*` release tag is
pushed, so every deployment identifies its exact source release rather than a branch. Configure
the repository's Pages custom domain as `www.telecrypt.io`.

The apex domain, `telecrypt.io`, is intentionally separate: it provides Matrix discovery and
redirects browser traffic to `www.telecrypt.io`. Matrix client, authentication, and control-plane
APIs are served at `https://backend.telecrypt.io`; Matrix IDs remain `@user:telecrypt.io`.
