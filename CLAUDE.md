# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Project context

The personal site of Anurag Das (anurag.gg), built on `FynePool/artist-portfolio-template`: a single-page portfolio deployed on Vercel, with Decap CMS for content editing. The template's placeholder content is gone; the stills are Pexels stand-ins, credited on the site, until the owner's photographs replace them. Optimize for small reviewable changes, accessibility, responsive UI, basic SEO, and working local build before deploy. No secrets in git.

## Design

The site is staged as a short picture in five parts, in the manner of a Wes Anderson title card. `design/DIRECTION.md` (untracked working folder) holds the reasoning; the rules that the code depends on are these:

- **Fields.** Every card sits on one flat colour field with one ink. The fields are the `.f-*` classes in [app/globals.css](app/globals.css) (`pink`, `marigold`, `turquoise`, `red`, `mint`, `cream`, `teal`), each setting `--field` and `--ink` as RGB triplets, with a deepened `.dark` variant. Text on a field is always `rgb(var(--ink))`, at reduced alpha for secondary text. A card declares its field twice: the class, and `data-field` (read by the header). The key type is `FieldKey` in [lib/types.ts](lib/types.ts); [lib/fields.ts](lib/fields.ts) validates keys and assigns a field by position when a work names none.
- **Cards.** `.card` is a full-viewport section with a double keyline (`::after`). `.stage` centres its content. Composition is symmetric on the vertical centre line: label, title, still.
- **The still.** [components/Still.tsx](components/Still.tsx) is the only way a photograph appears: a fixed window (`.frame`, 1.37:1, 3:4 on phones) with a keyline, and the work's note as a subtitle inside it (`.sub`). Subtitle yellow (`--sub`) is the one accent and has that one job; it never appears on a field.
- **Type.** One family, Jost (`--font-jost`), standing in for Futura. Capitals for titles, labels and navigation. The template's `font-serif` and `font-sans` both resolve to it.
- **Motion.** Every change of state is a cut. No entrance animation, no fades. The only animated things are the lightbox zoom and the Play progress segments.
- **Copy.** English, sentence case in content, no exclamation marks. A work's `title` is its part title; its `note` is its subtitle; `alt` describes the photograph.

## Template setup

Two entry points:

- **Plugin `artist-portfolio`** ([plugin/](plugin/), listed by [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json), so this repo is also a plugin marketplace): `/artist-portfolio:setup` bootstraps from nothing — prerequisites (incl. Vercel Hobby constraints), private repo from template (`gh repo create --template` or the "Use this template" link), Vercel project named by the user (connector or CLI), first commit, then hands off to the repo's `/setup` in a new session (repo skills only load in a session opened on the repo). Plugins don't load in cloud sessions; repo skills do. Bump `version` in [plugin/.claude-plugin/plugin.json](plugin/.claude-plugin/plugin.json) on every plugin change (it pins installs). Validate with `claude plugin validate .` and `claude plugin validate ./plugin`. [plugin/README.md](plugin/README.md) is the directory listing text and must disclose every service the skill acts on; [plugin/.claude-plugin/icon.png](plugin/.claude-plugin/icon.png) is the listing icon (the directory reads it only on the first portal save). Avoid download-and-run shell patterns in skills (`$(curl …)`, `$(gh api …)`, `… | sh`, clone-then-run chains): the directory lint flags them.
- **Repo skills** (below), usable locally or in a cloud session (`CLAUDE_CODE_REMOTE=true`: no Vercel CLI, no browser, no local files — use connectors).

Derived repos must not keep `plugin/` and `.claude-plugin/`: step 1.3 (`/setup-repo`) removes them and `check-setup` flags them.

Vercel Hobby constraints enforced by the setup: non-commercial use (showcase only), commits from the Vercel owner only on private repos (CMS editor = owner, git author = owner's GitHub noreply email), personal-account repos only.


A new project created from this template is configured through project skills in [.claude/skills/](.claude/skills/):

- `/setup` — orchestrator: inventories available tools (gh, Vercel CLI/connector, browser, Gmail), runs `npm run check-setup`, then runs the phases below in dependency order.
- `/setup-repo` → `/setup-content` → `/setup-vercel` → `/setup-cms` → `/setup-contact-form` (optional) → `/setup-domain` (optional).
- The canonical numbered step list is [.claude/skills/setup/progress-template.md](.claude/skills/setup/progress-template.md); `/setup` copies it to `setup-progress.md` (project root) and marks a step `[x]` only with verification evidence. `check-setup` parses that file and lists open steps. Keep step IDs consistent across the template, the phase skills and the README table.

`npm run check-setup` ([scripts/check-setup.mjs](scripts/check-setup.mjs)) is read-only and reports what is still template-default (artist name, placeholder galleries/samples, stock hero, default icon marker, CMS placeholders `OWNER/REPO` / `YOUR-SITE`, git origin still pointing at the template). Keep it in sync when adding new template placeholders.

Setup rules: confirm before outward actions (repo creation, deploys, env vars, invites); `OAUTH_CLIENT_SECRET` never passes through the conversation — the user sets it on Vercel.

## Tech stack

- Framework: Next.js 16 (App Router)
- Language: TypeScript 5 (strict)
- Package manager: npm
- Styling: Tailwind CSS v4
- Testing: none
- Deployment: Vercel (framework defaults — no `vercel.json`)

## Commands

```bash
npm install         # install dependencies
npm run dev         # dev server → http://localhost:3000
npm run build       # production build
npm run lint        # ESLint
npx tsc --noEmit    # typecheck (no dedicated script in package.json)
npm run check-setup # template setup status (read-only)
```

Before marking a task done, run the cheapest relevant check:
1. `npm run lint` for any JS/TS change
2. `npx tsc --noEmit` for type-affecting changes
3. `npm run build` before deploy-sensitive changes

## Key conventions

**CSS tokens** — Tailwind v4 defines semantic tokens in [app/globals.css](app/globals.css) (`surface`, `ink`, `body`, `muted`, `faint`, `rule`); they are the cream field and its ink, and the template's text sections (articles, exhibitions, contact) use them. Use these instead of Tailwind's built-in color classes. Dark mode redefines the same tokens under `.dark` on `<html>` — not a media query. The cards themselves use the field classes described under Design, and their layout classes live in the `@layer components` block of the same file.

**Content** — Copy is split across three files in [data/](data/), not a single `content.json` (no such file exists): [data/general.json](data/general.json) (`siteTitle`, `artistName`, `description`, `defaultTheme`), [data/bio.json](data/bio.json) (`bio`, `email`, `location`, `occupation`, `social`, `aboutSections`), [data/homepage.json](data/homepage.json) (`hero`, `sectionVisibility`, `sectionOrder`, `exhibitionsCta`). `hero` also carries `label`, `alt`, `credit`, `field` and `focus`. `social` keys are `github`, `instagram`, `x`, `facebook`, `website` (`SocialKey`). Bio paragraphs support `_text_` for italic. `defaultTheme` sets the initial theme (`"dark"` | `"light"`). `artistName` is the single source for the artist's name in nav, footer, page metadata, OG alts, JSON-LD and the `.ics` PRODID — never hardcode the name in components.

**Section system** — Two independent fields in [data/homepage.json](data/homepage.json) control homepage sections:
- `sectionOrder`: array that sets the render order. Hero is always first, Footer always last.
- `sectionVisibility`: object mapping each key to a **plain boolean** (`"galleries": true`, not `{ "show": true }`). A section is rendered **only** if its key is present here with value `true`. If the key is missing, the section is hidden regardless of `sectionOrder`.

Current valid section keys: `"galleries"`, `"articles"`, `"exhibitions-cta"`, `"about"`, `"contact"`, `"featured"`. `"galleries"` renders the parts and `"about"` the credits card; the other four are the template's sections, switched off here, and render on the cream field when switched on.

**Adding a new section** — When introducing a new homepage section:
1. Add its `SectionKey` to the union type in [app/page.tsx](app/page.tsx).
2. Add it to `sectionMap` in [app/page.tsx](app/page.tsx).
3. Add it to `sectionVisibility` in [data/homepage.json](data/homepage.json) (boolean `true`/`false`).
4. Optionally add it to `sectionOrder` to position it.
Skipping step 3 means the section will never render.

**Gallery auto-discovery** — [lib/data.ts](lib/data.ts) reads `public/assets/` at build time and derives all gallery sections and artwork metadata from folder/file names. No code changes are needed to add or remove **artwork within existing galleries**. See `/add-artwork` for naming conventions.

**Gallery folder = slug** — the folder name under `public/assets/galleries/` is **only** the URL slug (`/galleries/{folder}`): a clean kebab string matching `^[a-z0-9-]+$` (e.g. `section1`, `pittura`). No `{index}_{title}_{subtitle}` convention — that was removed (`parseFolder` no longer exists). Folders not matching the slug regex are skipped with a `console.warn` in `getGalleries()`. All mutable metadata (title, subtitle, order, visibility) lives in `gallery-config.json`, so renaming a gallery's title never changes its URL. Renaming the **folder** changes the URL — a rare developer action; add an explicit redirect in `next.config.ts` if the old URL was public.

**Adding a new gallery section** — **no developer action required**: the content manager creates it from the CMS ("Gallerie — Opere" → new entry). `npm run sync-cms` and the `BEGIN/END gallerie autogenerate` markers **no longer exist** — the two gallery collections in [public/admin/config.yml](public/admin/config.yml) are static and cover every gallery. Creating the folder by hand still works (`lib/data.ts` auto-discovers it), but `gallery.json` must then include `"type": "opere"` or the gallery won't show in the CMS (see below).

**Gallery CMS collections — why the `type` field exists** — the two collections (`gallery_opere`, `gallery_config`) are `folder` collections pointing at the **same** base folder `public/assets/galleries`. Decap does **not** scope a folder collection by filename: its listing filters only by extension and depth (`listEntries` → `entriesByFolder(folder, extension, depth)`; `depth` is a *maximum*). Without a discriminator each collection would list **both** `gallery.json` and `gallery-config.json`, and saving one under the other's schema would wipe its fields. The separation therefore comes from a top-level `"type"` field (`"opere"` / `"config"`) plus each collection's `filter` option, which matches on parsed JSON fields. **A gallery JSON without the right `type` is invisible in the CMS** (the site still renders it — `lib/data.ts` ignores `type`). The `nome` field is the slug source (`identifier_field` + `slug: "{{nome}}"`) and must match the folder name; in `gallery-config.json` it must match the gallery's folder or the config is silently ignored.

**Decap CMS** — Config at [public/admin/config.yml](public/admin/config.yml). Handles gallery metadata, articles, exhibitions, mostre, premi, and site settings. Auth via GitHub OAuth through `/api/auth` ([app/api/auth/route.ts](app/api/auth/route.ts), env `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET`). In the template `backend.repo` is `OWNER/REPO` and `base_url` / `site_url` are `https://YOUR-SITE.vercel.app`: placeholders filled by `/setup-repo` and `/setup-cms`.

**Navigation** — [components/Nav.tsx](components/Nav.tsx) is a server component that builds the links (one per public gallery from `getGalleries()`, pointing at `/galleries/{id}`, plus About / Elsewhere / Contact / Exhibitions) filtered by `sectionVisibility` and ordered by `sectionOrder`, and the parts Play runs through. [components/NavClient.tsx](components/NavClient.tsx) splits the links into two groups either side of the name, takes the field of whichever card is under the bar (`data-field`), shows the ornament in place of the name over a card marked `data-named`, and owns the phone menu. Pass `<Nav field>` the field of the page's first card.

**Gallery config (`gallery-config.json`)** — each gallery folder holds two sibling JSON files: `gallery.json` (`type: "opere"`, `nome`, `items`) and `gallery-config.json` (`type: "config"`, `nome`, gallery-level settings). They're deliberately **separate files, not one object**: a Decap folder-collection entry maps to exactly one file, and keeping them apart is what gives the content manager two distinct CMS screens (a gallery can hold ~50 works — merging config into that page would make it unusable). `gallery-config.json` fields (all optional):
- `title` / `subtitle` — visible identity; `title` absent ⇒ `kebabToWords(folder)`.
- `layout` — `"grid-3"` | `"grid-2"` set the column count of the stills grid on the gallery page; `"masonry"` (the parser's default) lays out as three columns, because every still sits in the same window. Read by [components/Gallery.tsx](components/Gallery.tsx); layout is never derived from the folder name.
- `order` — render order (ascending); absent ⇒ end of list, tie-break on folder name.
- `visibility` — `"public"` (default) | `"unlisted"` | `"draft"`. `public`: shown in homepage + dedicated page + sitemap/OG. `unlisted`: hidden from homepage but page/sitemap stay live. `draft`: excluded upstream in `getGalleries()` → 404 on `/galleries/{slug}`, out of sitemap/OG.
- `enabled` / `limitItems` — homepage preview: when `enabled` is `true`, the homepage shows only the first `limitItems` works as parts, and the last one links to `/galleries/{id}`; else every work is a part. Orthogonal to `visibility` (they decide *how* a visible gallery renders, not *whether*).
- `description` — free extended metadata.

`readGalleryConfig()` in [lib/data.ts](lib/data.ts) defaults every field at runtime (`{ enabled: false, limitItems: 6, order: +∞, visibility: "public", layout: "masonry" }`, title from folder) when `gallery-config.json` is missing or malformed — never assume it exists. A gallery is fully valid with `gallery.json` alone.

**Empty galleries are skipped** — `getGalleries()` drops any gallery with zero works. This keeps a just-created (still empty) gallery, or an orphan folder holding only a `gallery-config.json` saved under a mismatched `nome`, from rendering an empty section in production. `readWorks()` also tolerates a missing/non-array `items` (a CMS-created gallery may not serialize an empty list) — without that guard the build would throw.

**A gallery renders two ways** — on the homepage, [components/Parts.tsx](components/Parts.tsx) gives every work its own card ("Part n of N", title, still). On `/galleries/[id]`, [components/Gallery.tsx](components/Gallery.tsx) shows the same works as a grid of framed stills that open in the lightbox. Per-work fields beyond the template's (`title`, `note`, `field`, `credit`, `focus`) are parsed in `readWorks()`.

**Medium filter** — [lib/mediums.ts](lib/mediums.ts) (`uniqueMediums`, `filterByMedium`) + [components/MediumFilter.tsx](components/MediumFilter.tsx). Only active on [components/Gallery.tsx](components/Gallery.tsx) via `enableFilter`, on the `/galleries/[id]` page.

**Play** — [components/Screening.tsx](components/Screening.tsx) replaces the template's slideshow. It runs every public gallery's works as a picture: a part card (1.6 s), then the still with its subtitle (5 s), hard cuts, an end card, then the credits. It is mounted once by [components/NavClient.tsx](components/NavClient.tsx) and opened through [lib/screening.ts](lib/screening.ts) (`openScreening()`), which the header's Play button and the stills page's Play card (`enablePlay` on `Gallery`) both call. Space pauses, the arrows cut between parts, Escape stops. With `prefers-reduced-motion` it does not advance on a timer.

**Exhibition status & calendar export** — [lib/exhibitionStatus.ts](lib/exhibitionStatus.ts) derives current/upcoming/past from an exhibition's `date`/`dateEnd`; upcoming exhibitions get an "Aggiungi al calendario" link built by [lib/ics.ts](lib/ics.ts) and served from [app/exhibitions/[slug]/calendar.ics/route.ts](app/exhibitions/[slug]/calendar.ics/route.ts).

**JSON-LD (schema.org)** — [lib/jsonld.ts](lib/jsonld.ts) has pure builder functions (`buildPersonSchema`, `buildExhibitionEventSchema`, `buildVisualArtworkSchema`); rendered via [components/JsonLd.tsx](components/JsonLd.tsx) (a server component, no `'use client'`). Wired into `app/layout.tsx` (Person, every page), `app/exhibitions/page.tsx` (ExhibitionEvent[]), `app/galleries/[id]/page.tsx` (VisualArtwork[]). Build-time only, zero client JS.

**Dynamic OG images** — build-time `next/og` via the `opengraph-image.tsx` file convention, siblings of `app/page.tsx`, `app/exhibitions/page.tsx`, `app/galleries/[id]/page.tsx`. [lib/ogAssets.ts](lib/ogAssets.ts) picks the source image. No static OG image files or hardcoded URLs.

**Lightbox → Contact prefill** — [lib/contactPrefill.ts](lib/contactPrefill.ts) bridges [components/Lightbox.tsx](components/Lightbox.tsx)'s "Ask about this still" button to [components/Contact.tsx](components/Contact.tsx): scrolls to `#contact` and prefills the message. Falls back to a `mailto:` link if no Contact section is rendered on the current page. The button is hidden while `bio.email` is empty.

**Site URL** — [lib/site.ts](lib/site.ts) exports `SITE_URL`, the single source of truth for the production domain, resolved at build time from `NEXT_PUBLIC_SITE_URL` (optional override) → `VERCEL_PROJECT_PRODUCTION_URL` (Vercel system env) → `http://localhost:3000`. Imported by `metadataBase` in `app/layout.tsx`, `sitemap.ts`, `robots.ts`, `lib/ics.ts` and every JSON-LD/OG builder. Never hardcode the URL elsewhere (the only other place is the Decap `config.yml`, which can't read env vars).

**Path alias** — `@/*` resolves to the project root (`tsconfig.json`).

## Working rules

- Prefer minimal diffs; do not rewrite entire files unless unavoidable.
- Preserve existing visual behavior unless the task explicitly asks for redesign.
- Before editing, identify the files likely involved.
- For non-trivial changes, propose a short plan first.
- After editing, name the changed files and verification run.
- If a command fails, report the exact command and likely cause.
- Do not invent env vars, API routes, or data contracts not already in the codebase.
- Do not modify `.env*`, generated build output, or lockfiles without explicit reason.

## Vercel rules

- No `vercel.json` — rely on Next.js framework conventions.
- Preview and Production are separate environments; env var changes require a new deployment.
- Do not hardcode secrets or deployment URLs — [lib/site.ts](lib/site.ts) (`SITE_URL`) is the only code path for the production URL; everything else imports it.
- Env vars: `NEXT_PUBLIC_WEB3FORMS_KEY` (Production/Preview/Development, public by design), `OAUTH_CLIENT_ID` + `OAUTH_CLIENT_SECRET` (Production), optional `NEXT_PUBLIC_SITE_URL`. See [.env.example](.env.example).
- If local and Vercel builds diverge, compare Node version, env vars, and build command.

## Git rules

- Run `git status` before large changes.
- Do not mix unrelated changes in one commit.
- Never force-push or delete branches without explicit request.
