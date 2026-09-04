# Astrea Hosting Edition Plan

Status: proposed implementation plan. Build work starts only after explicit approval.

## Goal

Keep one visual/public React application while supporting two deployment editions from the same repository:

- **FULL edition** — existing VPS stack: React + FastAPI + PostgreSQL + protected full Admin + candidate workflow.
- **HOSTING edition** — shared-hosting stack: the same public React UI + PHP API + MySQL + a small protected **Astrea Lite Editor**.

The editions must not become two copied frontends. Public components, layout, styles, routes, brand assets and responsive behavior stay shared.

## Non-goals

- Do not remove, downgrade or rewrite the existing FastAPI/PostgreSQL implementation.
- Do not fork the React app into a second copied site.
- Do not require GitHub, JSON editing or manual rebuilds for normal client editorial work.
- Do not introduce WordPress or another general-purpose CMS.
- Do not activate a shared-hosting candidate workflow until its separate security/legal acceptance slice is approved.

## Architecture

```text
                         Shared React UI
                              |
                 +------------+------------+
                 |                         |
          HOSTING edition              FULL edition
                 |                         |
             PHP API                    FastAPI
                 |                         |
              MySQL                   PostgreSQL
                 |                         |
         Astrea Lite Editor            Full Admin
```

### Contract strategy

Prefer compatibility over parallel application logic. The PHP API should expose response shapes close to the accepted FastAPI public/content contracts so public React pages can use the same data types and rendering code.

A build-time edition setting may choose runtime capabilities, for example:

```text
VITE_ASTREA_EDITION=full
VITE_ASTREA_EDITION=hosting
```

The exact variable name is implementation detail; there must be one explicit edition contract, validated at build time.

FULL remains the default unless the hosting build command explicitly selects HOSTING.

## Hosting edition content model

### 1. Predefined pages

Editable fixed pages remain available:

- about
- lodges_spb
- principles
- faq
- contacts
- materials intro/landing copy

The client edits title, text and publication state through Lite Editor.

### 2. News

Client can:

- create;
- edit;
- publish/unpublish;
- delete;
- set slug, title, excerpt, body and image.

Public behavior remains compatible with the current `/novosti` and `/novosti/:slug` routes.

### 3. Materials

Materials become a real editorial collection rather than only a landing link.

Client can create/edit/publish/delete material articles with a schema deliberately close to News:

- slug;
- title;
- excerpt;
- body;
- optional image;
- publication state/date.

`/materialy` remains the landing/index route and may continue exposing the existing News/Video cross-links while also listing published material articles.

A safe detail route will be added, preferably `/materialy/:slug`.

### 4. Video

Client can create/edit/publish/delete video records using the accepted RuTube-oriented model:

- title;
- description;
- source URL;
- publication state.

Provider/embed data remains server-derived. Arbitrary iframe/HTML input is not accepted.

### 5. Additional standalone pages

The client requirement includes adding pages, not only editing predefined ones. Implement this as a separate controlled `custom_pages` content type instead of weakening the immutable predefined-page contract.

Initial safe public route:

```text
/stranicy/:slug
```

Client can create/edit/publish/delete custom pages. Automatic top-navigation editing is out of the first slice; navigation management can be added later if actually needed.

This model should also be portable later into FULL edition instead of creating HOSTING-only content that cannot migrate.

## Astrea Lite Editor

The client must not edit files, JSON, SQL or GitHub.

Lite Editor is a protected web UI with simple forms and the minimum navigation needed for editorial work:

- Overview
- News
- Materials
- Video
- Pages
- Images/media where required

Normal workflow:

```text
Open editor -> edit/create -> Save or Publish -> content is immediately visible
```

No manual frontend rebuild after an editorial change.

For the first version, body content remains plain text with preserved line breaks, matching the current safe rendering model. No raw HTML editor and no `dangerouslySetInnerHTML`.

## Lite Editor authentication and security baseline

Required before acceptance:

- server-side PHP session;
- `HttpOnly` session cookie;
- `SameSite=Strict`;
- `Secure` in HTTPS production;
- CSRF protection for writes;
- password stored only through PHP `password_hash` / `password_verify`;
- no credentials in repository;
- no public registration;
- no password in browser storage;
- login rate limiting / throttling;
- PDO prepared statements only;
- generic production errors without SQL/config leakage;
- protected editor endpoints excluded from indexing.

Production configuration containing DB credentials is created on the host and is not committed.

## Editorial image uploads

Editorial images are public assets, unlike candidate photographs.

Upload baseline:

- explicit MIME allowlist;
- size limit;
- image validation with server-supported PHP facilities;
- generated non-user-controlled filenames;
- no executable extensions;
- upload directory configured so scripts cannot execute;
- path traversal protection;
- old-file cleanup only when safe and explicit.

Do not assume Imagick/GD availability until the real Timeweb PHP environment is checked. The implementation must degrade safely if server-side re-encoding is unavailable.

## Candidate Lite — separate controlled slice

Candidate intake is not part of the first editorial Hosting build.

The public candidate page may remain present but disabled until Candidate Lite is separately approved.

Before Candidate Lite activation, verify the shared-hosting environment and define:

- server-side validation equivalent to the accepted public contract where practical;
- consent evidence/versioning;
- anti-spam/rate limits;
- private candidate-photo storage that is not directly web-readable;
- protected Lite Editor candidate access;
- retention/deletion policy;
- whether notification is email-only or DB + email;
- mail transport available on the real host;
- no candidate PII in logs/URLs/browser storage.

Existing legal texts/version identifiers are not changed by this project slice.

FULL candidate workflow remains untouched and disabled/activated under its existing gates.

## MySQL portability rules

Hosting schemas should deliberately preserve the conceptual FULL models so migration later is deterministic.

At minimum preserve:

- stable slugs/keys;
- title/body/excerpt semantics;
- publication state and timestamps;
- source image URL/path;
- RuTube source URL semantics.

Provide an import/export path later:

```text
HOSTING MySQL -> validated export -> FULL PostgreSQL import
```

Do not couple public URLs to MySQL numeric IDs when a stable key/slug exists.

## Proposed repository layout

```text
frontend/                 # shared React UI for both editions
backend/                  # existing FULL FastAPI backend, preserved
hosting/
  api/                    # PHP API/router/controllers
  config/                 # safe config templates, no secrets
  db/                     # MySQL schema/migrations/install SQL
  public/                 # shared-hosting entry/rewrite files as needed
  tests/                  # PHP/API contract checks where practical
  README.md               # local/deploy/operator notes
infra/                    # existing FULL/VPS deployment
```

Exact PHP file layout may be adjusted during implementation, but HOSTING code stays isolated under `hosting/` except for intentional shared frontend/build changes.

## Shared-hosting routing

HOSTING must support React Router deep links and PHP API routing on Apache-compatible hosting.

Provide reviewed `.htaccess` rules that:

1. never rewrite API/editor-media requests to `index.html`;
2. route PHP API requests to the PHP entry point;
3. route public SPA paths to `index.html` only when the file/directory does not exist;
4. deny direct access to config/private paths;
5. deny script execution inside public upload directories.

Rules must be validated against the actual Timeweb hosting behavior before production acceptance.

## Build profiles

Add an explicit HOSTING build command, conceptually:

```text
npm run build:hosting
```

It should produce a deployable shared-hosting artifact containing only what the hosting edition requires.

The normal FULL build remains available and must continue to pass existing CI.

HOSTING build must not accidentally ship privileged FULL-only routes/configuration as an assumed security boundary. Backend authorization remains authoritative even if routes are omitted from the UI.

## Implementation slices

### H0 — Architecture freeze

- approve this plan;
- record Hosting/FULL edition decision in project documentation;
- confirm real hosting supports required PHP/MySQL/Apache rewrite capabilities before deployment, not by assumption.

### H1 — Edition/build foundation

- add edition configuration and `build:hosting`;
- preserve FULL as existing default;
- add hosting package layout and safe config templates;
- add CI checks for both frontend build modes;
- add rewrite/routing skeleton without candidate activation.

Acceptance: FULL remains unchanged and green; HOSTING artifact builds deterministically.

### H2 — PHP/MySQL public content foundation

- MySQL schema/migrations for pages, custom pages, news, materials, videos;
- PHP DB/config bootstrap;
- published-only public endpoints;
- stable validation and error contracts;
- no editor yet.

Acceptance: public HOSTING APIs return only published content and match the agreed frontend contract.

### H3 — Lite Editor editorial administration

- authentication/session/CSRF;
- editor overview;
- CRUD for news/materials/video/custom pages;
- update predefined pages;
- publication controls;
- editorial image upload;
- no candidate access yet.

Acceptance: client can manage normal site content without files/Git/SQL/rebuilds.

### H4 — Shared frontend integration

- make current public pages consume HOSTING APIs in hosting mode while preserving FULL behavior;
- add material article listing/detail;
- add custom page route;
- expose Lite Editor route/build only for HOSTING;
- verify desktop/mobile parity with the accepted design.

Acceptance: public HOSTING site is visually equivalent to FULL for shared pages/content.

### H5 — Candidate Lite security slice

Only after separate explicit approval:

- hosting candidate endpoint;
- private persistence/photo handling;
- protected Lite Editor candidate list/detail;
- consent evidence;
- anti-spam/rate limiting;
- mail/readiness decision;
- controlled E2E.

Acceptance: candidate activation is fail-closed until all agreed security/legal checks pass.

### H6 — Timeweb release package and deployment acceptance

- create upload-ready HOSTING artifact;
- installation/config instructions;
- DB initialization/bootstrap procedure;
- HTTPS/origin/SEO settings;
- smoke checklist;
- backup/export procedure;
- production deploy only with explicit approval.

## CI expectations

Existing required gates remain green.

Add HOSTING-specific checks incrementally, including where practical:

- PHP syntax/lint;
- deterministic schema validation;
- public/editor API contract tests;
- hosting frontend typecheck/lint/build;
- no committed secrets;
- `.htaccess`/package structure checks;
- ensure candidate hosting route remains unavailable before H5 approval.

## Release strategy

The first deploy target is HOSTING edition on the client's existing shared hosting/domain strategy.

FULL edition remains production-ready source code for later VPS migration. When the client later moves to FULL:

1. export validated Hosting content;
2. import into PostgreSQL;
3. point the shared React frontend at FULL APIs/build;
4. switch DNS/origin;
5. perform redirects/canonical/sitemap cutover;
6. retire HOSTING backend only after acceptance.

## Decision required before Build

Approve or amend this plan. After approval, implementation starts from fresh `main` in `feat/hosting-edition` and proceeds H1 -> H4 first. H5 Candidate Lite remains a separate explicit approval gate.