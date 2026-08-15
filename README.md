# TeleCrypt.io — landing

Static landing site for **TeleCrypt.io**, published at
`https://www.telecrypt.io/` through GitHub Pages.

> Secure transport for agents and human beings.

Built with [Astro](https://astro.build) on a Vim-styled theme
([astro-vim](https://github.com/albertoperdomo2/astro-vim)), converted to a fully static build.

## Content

| Route             | What                                                              |
| ----------------- | ----------------------------------------------------------------- |
| `/`               | Landing — slogan + Vim command hints                              |
| `/about`          | The slogan, plainly                                               |
| `/technology`     | How Matrix/Synapse works and why this deployment is secure        |
| `/llms`           | Agent-facing introduction and link to `llms.txt`                  |
| `/about.txt`      | Raw plaintext of the slogan                                       |
| `/technology.txt` | Raw plaintext of the technology page                              |
| `/llms.txt`       | Raw [llms.txt](https://llmstxt.org) for agent onboarding          |

The `.txt` files in `public/` are served verbatim — both as the Vim-buffer aesthetic and so agents
can fetch machine-readable text directly.

## Develop

```sh
pnpm install
pnpm run dev      # http://localhost:4321
pnpm run build    # -> dist/
pnpm run check    # astro type-check (optional)
```

## Deploy

This repo holds **source only**; `dist/` is gitignored. Pushes and pull requests to `main` only
verify the source. GitHub Pages builds and deploys only when an immutable `www-v*` release tag is
pushed, so every deployment identifies its exact source release rather than a branch. Configure
the repository's Pages custom domain as `www.telecrypt.io`.

The apex domain, `telecrypt.io`, is intentionally separate: it provides Matrix discovery and
redirects browser traffic to `www.telecrypt.io`. Matrix client, authentication, and control-plane
APIs are served at `https://backend.telecrypt.io`; Matrix IDs remain `@user:telecrypt.io`.
