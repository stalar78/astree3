# Astrea Hosting Edition Plan

Status: approved product direction; build authorized by user on 2026-09-04 after client scope clarification.

## Product goal

The HOSTING edition exists to solve four concrete client problems, not to become a general-purpose CMS:

1. Show that the lodge is active by publishing a small number of lodge news items each year.
2. Give a candidate a compact set of introductory materials: a few books, videos, audio/podcast items and, if needed, articles.
3. Preserve the accepted visual language and sense of mystery/closedness through the symbolic rail and restrained presentation.
4. Make dates of works/events and the Saint Petersburg location obvious enough that visitors understand where the lodge operates before applying.

## Editions

Keep one visual/public React application while supporting two deployment editions from the same repository:

- **FULL edition** — existing VPS stack: React + FastAPI + PostgreSQL + protected full Admin + existing candidate workflow.
- **HOSTING edition** — shared-hosting stack: the same public React UI + PHP API + MySQL + protected **Astrea Lite Editor**.

The editions must not become two copied frontends. Public components, layout, styles, routes, brand assets and responsive behavior stay shared.

## Non-goals

- Do not remove, downgrade or rewrite the existing FULL implementation.
- Do not fork React into a copied second site.
- Do not require the client to edit JSON, GitHub, SQL or rebuild the frontend after normal editorial changes.
- Do not introduce WordPress or another general-purpose CMS.
- Do not build arbitrary custom-page creation in the first HOSTING release.
- Do not build roles, member areas or symbol-based access control in the first HOSTING release.
- Do not activate shared-hosting candidate intake until a separate security/legal slice is explicitly approved.

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

Prefer compatibility over parallel application logic. The PHP public API should expose response shapes close to the accepted FastAPI contracts where that is useful, while HOSTING-only content types may have their own narrow contracts.

Use one explicit build-time edition contract, conceptually:

```text
VITE_ASTREA_EDITION=full
VITE_ASTREA_EDITION=hosting
```

FULL remains the default. HOSTING is selected only by an explicit hosting build command.

## HOSTING MVP content model

### 1. News

This is the primary editorial workflow. The client expects only a few news posts per year, but must be able to manage them without technical help.

Lite Editor supports:

- create;
- edit;
- publish/unpublish;
- delete;
- slug;
- title;
- excerpt;
- body;
- optional image;
- publication timestamp.

Public behavior remains compatible with `/novosti` and `/novosti/:slug`.

### 2. Materials

Use one unified `materials` collection rather than separate mini-CMS modules for books, videos, audio and articles.

Each material has:

- type: `book | video | audio | article`;
- slug;
- title;
- short description;
- optional body;
- optional author;
- optional external/source URL;
- optional public media/image path;
- publication state/date;
- optional sort/order value.

Type-specific expectations:

- **book** — title, author, recommendation text, optional external link;
- **video** — title, description, safe source URL; embed/provider data is server-derived when embedding is supported;
- **audio** — title, description and either an allowed uploaded audio asset or external source URL;
- **article** — title, excerpt/body and optional image/source URL.

`/materialy` becomes the candidate-oriented materials index. A safe detail route may be added for article-like records when needed. The existing `/video` public route may remain as a filtered presentation of published `video` materials in HOSTING mode so the accepted public navigation does not regress.

No arbitrary iframe/HTML input is accepted.

### 3. Events / calendar

Events are a first-class HOSTING MVP content type because the client explicitly wants visitors to understand when lodge works and other events occur.

Each event has:

- title;
- event date;
- optional end date/time only if later required;
- short public note;
- type/category such as lodge work, feast or other event;
- publication state.

The accepted five-month calendar rail remains visually intact but can mark published event dates. Event information must also remain understandable on layouts where the desktop calendar rail is hidden; therefore the shared frontend will expose a compact upcoming-events presentation, not rely on color/hover alone.

### 4. Predefined pages

The Lite Editor may update only the existing predefined site pages needed by the public site, including the existing managed keys such as:

- about;
- lodges_spb;
- principles;
- faq;
- contacts;
- materials intro/landing copy.

The client may edit title, text and publication state.

Creating arbitrary standalone pages and editing top navigation are out of the first HOSTING release.

## Saint Petersburg clarity

The existing public design already references Saint Petersburg. The HOSTING integration must preserve and strengthen this where necessary, especially on candidate-facing content.

Acceptance requires that a visitor can understand before submitting an application that D.L. Astrea No. 3 operates in Saint Petersburg. Do not solve this with location tracking or geoblocking.

## Symbol rail / mystery

The accepted five-symbol rail remains a deliberate visual element. In the first HOSTING release:

- symbols remain decorative/ambiguous unless a separately approved interaction is added;
- no member authorization or hidden-member content system is introduced;
- inaccessible-looking symbolism is a design device, not a fake security boundary;
- desktop geometry must not be casually changed.

## Astrea Lite Editor

The editor is intentionally small and task-oriented.

Primary navigation:

```text
Overview
News
Materials
Events
Pages
```

Normal workflow:

```text
Open editor -> create/edit -> Save or Publish -> public site updates immediately
```

The client must never need GitHub, JSON, SQL or a frontend rebuild for those tasks.

For the first version, textual body content remains plain text with preserved line breaks or an equivalently safe limited editor. No raw HTML editor and no `dangerouslySetInnerHTML`.

## Authentication and security baseline

Required before Lite Editor acceptance:

- server-side PHP session;
- `HttpOnly` session cookie;
- `SameSite=Strict`;
- `Secure` in HTTPS production;
- CSRF protection for writes;
- password stored only with PHP `password_hash` / `password_verify`;
- no credentials in repository;
- no public registration;
- no password/token in browser storage;
- login throttling;
- PDO prepared statements only;
- generic production errors without SQL/config leakage;
- editor endpoints excluded from indexing;
- authorization enforced server-side, not by hiding React routes.

Production DB credentials are host configuration and are never committed.

## Editorial uploads

Public editorial media is distinct from candidate private photos.

Image/audio upload baseline:

- explicit extension and MIME allowlists;
- strict size limits;
- generated non-user-controlled filenames;
- no executable extensions;
- upload directories configured so scripts cannot execute;
- path traversal protection;
- server validation using available PHP facilities;
- safe failure if optional GD/Imagick/media tooling is unavailable;
- destructive old-file cleanup only when deliberate and safe.

Actual shared-hosting PHP limits and available extensions must be checked before production acceptance.

## Candidate intake — separate future slice

Candidate submission is not required to launch the first HOSTING editorial MVP.

The public candidate page may remain visible with intake disabled. Existing legal texts/version identifiers are not changed by this phase.

A later Candidate Lite slice requires separate explicit approval and must define, at minimum:

- server-side validation;
- consent evidence/versioning;
- anti-spam/rate limits;
- private non-web-readable candidate-photo storage;
- protected candidate list/detail access;
- retention/deletion rules;
- mail transport/readiness;
- no candidate PII in logs/URLs/browser storage.

The FULL candidate workflow remains untouched.

## MySQL portability

HOSTING data should remain portable toward FULL where practical.

Preserve stable slugs/keys, publication state, timestamps, media paths/source URLs and explicit material/event types. A later migration path may be:

```text
HOSTING MySQL -> validated export -> FULL import
```

FULL may require a future material/event schema extension before importing HOSTING-only types; that future extension is not part of this MVP.

## Proposed repository layout

```text
frontend/                 # shared React UI for both editions
backend/                  # existing FULL FastAPI backend, preserved
hosting/
  api/                    # PHP API/router/controllers
  config/                 # safe config templates, no secrets
  db/                     # MySQL schema/migrations/install SQL
  public/                 # Apache/shared-hosting rewrite/entry files
  tests/                  # PHP/API contract checks where practical
  README.md               # local/deploy/operator notes
infra/                    # existing FULL/VPS deployment
```

HOSTING code stays isolated under `hosting/` except for intentional shared frontend/build changes.

## Shared-hosting routing

Provide reviewed Apache-compatible `.htaccess` behavior that:

1. never rewrites API/editor/media requests to `index.html`;
2. routes PHP API requests to the PHP entry point;
3. routes SPA deep links to `index.html` only when the file/directory does not exist;
4. denies direct access to config/private paths;
5. denies script execution in public upload directories.

The exact rules must be validated on the real Timeweb hosting before production acceptance.

## Build profiles

Add an explicit HOSTING build command, conceptually:

```text
npm run build:hosting
```

The normal FULL build remains available and must continue to pass existing CI.

The HOSTING artifact must not rely on omission of FULL-only UI routes as a security boundary; PHP authorization remains authoritative.

## Implementation slices

### H0 — Architecture freeze

- record this approved four-goal client MVP;
- merge the plan;
- preserve FULL as a separate future deployment edition.

### H1 — Edition/build foundation

- add validated edition configuration;
- add `build:hosting` while preserving the current FULL build as default;
- create the hosting package layout and safe config templates;
- add CI checks for the HOSTING frontend build/package skeleton;
- add Apache rewrite/routing skeleton;
- keep candidate intake disabled.

Acceptance: FULL remains green and behaviorally unchanged; HOSTING builds deterministically without requiring FastAPI/PostgreSQL at runtime.

### H2 — PHP/MySQL public content foundation

- MySQL schema for news, materials, events, predefined pages and editor account/bootstrap data;
- PHP config/DB bootstrap;
- published-only public endpoints;
- stable validation/error contracts;
- no editor writes yet.

Acceptance: public HOSTING APIs expose only published content and support the shared frontend contract.

### H3 — Lite Editor

- login/session/CSRF/throttling;
- Overview;
- News CRUD;
- Materials CRUD with `book/video/audio/article` type;
- Events CRUD;
- predefined-page editing;
- editorial image/audio upload where supported;
- publication controls;
- no candidate module.

Acceptance: client can perform the four agreed editorial tasks without files/Git/SQL/rebuilds.

### H4 — Shared frontend integration

- connect current public pages to HOSTING APIs in hosting mode while preserving FULL behavior;
- make `/materialy` display candidate-oriented materials;
- preserve `/video` by filtering/mapping video materials if appropriate;
- connect published events to the accepted calendar and a mobile-accessible upcoming-events presentation;
- preserve/strengthen Saint Petersburg messaging on candidate-facing UI;
- verify desktop/mobile visual parity with the accepted design.

Acceptance: HOSTING public site meets the four client goals and visually remains the accepted Astrea design.

### H5 — Timeweb package and deployment acceptance

- upload-ready HOSTING artifact;
- installation/config instructions;
- MySQL initialization/bootstrap procedure;
- HTTPS/origin/SEO settings;
- smoke checklist;
- backup/export procedure;
- validate actual PHP/MySQL/Apache limits on the account;
- production deploy only with explicit approval.

### Future H6 — Candidate Lite

Only after separate explicit approval:

- hosting candidate endpoint;
- private persistence/photo handling;
- protected candidate access;
- consent evidence;
- anti-spam/rate limiting;
- mail readiness;
- controlled E2E.

## CI expectations

Existing required gates remain green.

Add HOSTING-specific checks incrementally, where practical:

- PHP syntax/lint;
- schema validation;
- public/editor API contract tests;
- hosting frontend typecheck/lint/build;
- no committed secrets;
- package/rewrite structure checks;
- candidate HOSTING endpoint remains unavailable before Future H6 approval.

## Release strategy

The first deployment target is HOSTING edition on the client's existing shared hosting. FULL remains production-ready source code for a later VPS migration.

The HOSTING release is accepted when the client can independently:

- publish a lodge news item;
- add/update recommended books/video/audio/article material;
- add/change a public lodge event date and see it reflected for visitors;
- edit the predefined public copy needed for the site;
- do all of the above without touching source files or rebuilding the frontend.

The public site must also preserve the accepted symbolic design and clearly communicate Saint Petersburg as the lodge location.