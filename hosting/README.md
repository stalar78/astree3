# Astrea HOSTING Edition

This directory contains the shared-hosting backend/package layer for the approved Astrea HOSTING edition.

Current implementation stage: **H3B Lite Editor content CRUD**. Public read APIs are available from H2, H3A provides the protected authentication/session shell, and H3B adds the four approved editorial workflows. Final frontend HOSTING integration and Timeweb packaging remain later slices.

## Runtime target

- existing shared React frontend built with `npm run build:hosting`;
- Apache-compatible shared hosting;
- PHP 8.x backend under `/api`;
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
- `scripts/` — CLI-only operational/bootstrap commands;
- `config/` — safe templates only; production/local credentials are never committed;
- `db/` — MySQL schema/migrations;
- `public/` — Apache/shared-hosting routing templates;
- `tests/` — HOSTING contract/security checks.

## Configuration

`config/config.example.php` is a non-secret template. A real installation will use `config/config.local.php`, which is ignored by Git and must stay outside public reach in the final Timeweb package.

For CI/local automation the database settings may be supplied through:

```text
ASTREA_HOSTING_DB_DSN
ASTREA_HOSTING_DB_USER
ASTREA_HOSTING_DB_PASSWORD
```

No production credentials belong in Git.

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

Editorial binary uploads are not implemented in H3B. News may use an optional HTTPS image URL and materials may use approved external/source URLs. Upload support must be capability-checked against the real shared-hosting PHP limits before production acceptance rather than assumed.

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

The bootstrap refuses to create a second account. H5 will document the exact Timeweb invocation and configuration placement.

## Expected final document-root shape

H5 will build the upload-ready package. Conceptually the hosting document root will contain:

```text
index.html
assets/
brand/
media/
api/
editor/
.htaccess
```

Private configuration/database bootstrap sources are not to be exposed as public static files. Candidate submission paths remain absent until a separately approved future Candidate Lite slice.
