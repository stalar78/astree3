# Astrea HOSTING Edition

This directory contains the shared-hosting backend/package layer for the approved Astrea HOSTING edition.

Current implementation stage: **H5 Timeweb packaging and deployment acceptance preparation**. H2 provides published-only PHP/MySQL read APIs, H3A/H3B provide the protected Lite Editor and the four approved editorial workflows, H4 connects HOSTING materials/events to the accepted shared React public UI, and H5 now provides the upload-package builder, capability preflight and Timeweb deployment runbook. Real account validation and production cutover remain separate operational actions and are not authorized by this repository state.

## Runtime target

- existing shared React frontend built with `npm run build:hosting`;
- Apache-compatible shared hosting with Nginx possibly serving static files in front of Apache;
- PHP 8.2+ backend under `/api`;
- MySQL persistence;
- protected server-rendered Astrea Lite Editor under `/editor/`;
- no FastAPI/PostgreSQL runtime requirement for the HOSTING edition.

The existing `backend/` and `infra/` directories remain the FULL/VPS edition and are not replaced by this package.

## Client-facing MVP

Lite Editor is limited to the agreed tasks:

- News;
- Materials (`book`, `video`, `audio`, `article`);
- Events / calendar;
- predefined Pages.

Arbitrary page creation and member-role functionality are out of the first release.

Candidate intake is deliberately **not part of the current HOSTING MVP**. The hosting build forces the public candidate form off until a separate security/legal slice is approved.

## Source layout

- `api/` — PHP bootstrap, published-only public queries and router;
- `editor/` — protected Lite Editor authentication, content validation and server-rendered UI;
- `scripts/` — CLI-only bootstrap/preflight plus the H5 package builder;
- `config/` — safe templates only; production/local credentials are never committed;
- `db/` — MySQL schema/migrations;
- `public/` — Apache/shared-hosting routing templates;
- `tests/` — HOSTING contract/security checks;
- `DEPLOY_TIMEWEB.md` — account/deployment runbook for H5.

## Configuration

`config/config.example.php` is a non-secret template. Source-tree development may use ignored `hosting/config/config.local.php`. The H5 deployment package instead keeps the real configuration at:

```text
<site>/private/config/config.local.php
```

while the PHP runtime lives under:

```text
<site>/public/
```

This is intentional. On shared hosting, private SQL/config/operator files must be physically outside the web document root instead of relying on `.htaccess` as a secrecy boundary.

For CI/local automation the database settings may also be supplied through:

```text
ASTREA_HOSTING_DB_DSN
ASTREA_HOSTING_DB_USER
ASTREA_HOSTING_DB_PASSWORD
```

No production credentials belong in Git, generated release artifacts, logs or prompts.

The production editor session is configured with an `HttpOnly` cookie, `SameSite=Strict` and `Secure=true`. Local HTTP development may override `secure` only in ignored local configuration.

## Database

Apply migrations in order:

```text
hosting/db/001_initial.sql
hosting/db/002_editor_auth.sql
```

They are idempotent for the intended installation/re-application checks.

Core tables:

- `pages` — six immutable/predefined public page keys;
- `news` — lodge news;
- `materials` — unified `book | video | audio | article` collection;
- `events` — public calendar dates;
- `editor_users` — Lite Editor accounts, with no seeded credentials;
- `editor_login_attempts` — hashed-client login throttling data;
- `hosting_schema_migrations` — HOSTING schema version markers.

The predefined pages are seeded unpublished with the same keys used by the FULL edition.

## Public API — H2

The PHP public API is read-only and returns only rows explicitly marked published.

```text
GET /api/health
GET /api/v1/health
GET /api/v1/pages/{key}
GET /api/v1/news
GET /api/v1/news/{slug}
GET /api/v1/materials
GET /api/v1/materials/{slug}
GET /api/v1/videos
GET /api/v1/videos/{id}
GET /api/v1/events
```

Lists accept bounded `limit`/`offset`. Materials may be filtered with `?type=book|video|audio|article`. Events accept optional ISO date bounds.

The `/videos` contract is derived from published `video` materials and accepts only canonical HTTPS RuTube URLs matching the FULL-edition provider model. Arbitrary iframe/HTML is never exposed.

## Lite Editor — H3A/H3B

`/editor/` provides the protected editor shell, overview and task-oriented content management for:

- News — create, edit, publish/unpublish and delete;
- Materials — create, edit, publish/unpublish and delete for `book`, `video`, `audio` and `article`;
- Events — create, edit, publish/unpublish and delete;
- Pages — edit only the six predefined page keys; arbitrary page creation is not exposed.

All state-changing editor actions require the authenticated PHP session and a valid CSRF token. Destructive UI actions require an explicit deletion confirmation. Server-side validation controls slugs, dates, material/event types and external URLs. Video materials require a valid RuTube HTTPS URL. Public API isolation remains authoritative: drafts are not returned publicly.

Editorial binary uploads are not implemented in the current HOSTING MVP. News may use an optional HTTPS image URL and materials may use approved external/source URLs. The H5 preflight records upload-related PHP capabilities for a possible future slice without enabling uploads now.

Security baseline already active:

- PHP server-side session;
- `HttpOnly` cookie;
- `SameSite=Strict`;
- `Secure` cookie in production configuration;
- session-id rotation on login/logout;
- eight-hour idle expiry;
- CSRF token for authenticated writes/logout;
- `password_hash` / `password_verify` only;
- generic login errors;
- login throttling after repeated failures;
- only a SHA-256 client key is stored for throttle state, not the plain IP address;
- `noindex`/`nofollow`, no-store and restrictive editor response headers;
- no public registration.

No editor account is seeded by migrations. One initial account is created explicitly with the CLI-only bootstrap command, which reads the password from standard input rather than command-line arguments:

```text
php hosting/scripts/bootstrap-editor.php <username>
```

The bootstrap refuses to create a second account. In an H5 package the same script is installed under `private/scripts/` and locates the sibling public runtime without putting credentials or password values in CLI arguments.

## Shared public frontend — H4

The React public site stays shared between FULL and HOSTING. HOSTING-only requests are guarded by the explicit edition setting so the default FULL build does not call HOSTING-only materials/events endpoints.

In HOSTING mode:

- `/materialy` loads the published unified materials collection and presents books, video, audio/podcast items and articles in the accepted reference styling;
- the managed `materials` page still controls the editable introduction/title without requiring a rebuild;
- `/video` keeps using the accepted public video contract, which the PHP layer derives from published `video` materials;
- the five-month desktop calendar marks published event dates while retaining its accepted geometry;
- mobile/tablet layouts, where the calendar rail is hidden, show a compact textual list of upcoming published events;
- event markers have a visible shape/legend and accessible labels rather than relying on hover or color alone;
- the existing public Saint Petersburg wording remains preserved, including the homepage lodge heading and candidate confirmation language.

Normal publication remains immediate: an editor can publish or change approved content in Lite Editor and the public HOSTING UI reads the updated data on the next request without GitHub, SQL or a frontend rebuild.

## H5 package builder

Build the deployment artifact only with the final intended HTTPS origin:

```bash
npm --prefix frontend ci
node hosting/scripts/build-package.mjs --origin=https://example.org
```

The origin is validated as a bare HTTPS origin and is used for the static SEO artifact. The generated release is written to the ignored directory:

```text
hosting/release/astrea-hosting/
├── public/
│   ├── index.html
│   ├── assets/
│   ├── brand/
│   ├── media/
│   ├── api/
│   ├── editor/
│   ├── .htaccess
│   ├── robots.txt
│   └── sitemap.xml
├── private/
│   ├── config/
│   ├── db/
│   └── scripts/
├── DEPLOY_TIMEWEB.md
└── manifest.json
```

The builder validates that required runtime/operator files exist, rejects leakage of real config/SQL artifacts into `public/`, verifies that HOSTING candidate runtime is absent, and checks that the generated sitemap contains the configured origin.

CI builds the package against a non-production test origin and verifies the public/private boundary. That CI package is a contract test only; it is not a production artifact because production SEO must be built with the actual final origin.

## H5 capability preflight

Before deployment, run:

```bash
php private/scripts/preflight.php
```

It verifies PHP 8.2+, required PHP extensions and reports relevant hosting limits. After installing the private configuration and applying MySQL migrations, run:

```bash
php private/scripts/preflight.php --check-db
```

The database mode verifies connection, required tables and migration markers without printing credentials.

## Timeweb deployment

The detailed operator sequence is in [`DEPLOY_TIMEWEB.md`](./DEPLOY_TIMEWEB.md). The intended production topology is:

```text
<site>/
├── public/       # the only web document root / public_html target
└── private/      # config, schema and operator scripts; never web-visible
```

The real Timeweb account must still be checked for its selected PHP version/extensions, MySQL version, actual document-root/symlink behavior, rewrite behavior, HTTPS origin, runtime limits, backup/export and public/editor smoke tests.

**Repository H5 completion does not authorize a production cutover.** Uploading/changing the live hosting account remains a separate destructive/operational action and requires explicit approval after the account-specific preflight is recorded.
