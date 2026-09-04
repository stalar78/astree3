# Astrea HOSTING Edition

This directory contains the shared-hosting backend/package layer for the approved Astrea HOSTING edition.

Current implementation stage: **H2 public content foundation**. It is not yet production-deployable because Lite Editor writes/authentication and final Timeweb packaging are later slices.

## Runtime target

- existing shared React frontend built with `npm run build:hosting`;
- Apache-compatible shared hosting;
- PHP 8.x backend under `/api`;
- MySQL persistence;
- protected Astrea Lite Editor added in H3;
- no FastAPI/PostgreSQL runtime requirement for the HOSTING edition.

The existing `backend/` and `infra/` directories remain the FULL/VPS edition and are not replaced by this package.

## Client-facing MVP

Lite Editor will be limited to the agreed tasks:

- News;
- Materials (`book`, `video`, `audio`, `article`);
- Events / calendar;
- predefined Pages.

Arbitrary page creation and member-role functionality are out of the first release.

Candidate intake is deliberately **not part of the current HOSTING MVP**. The hosting build forces the public candidate form off until a separate security/legal slice is approved.

## Source layout

- `api/` — PHP bootstrap, published-only public queries and router;
- `config/` — safe templates only; production/local credentials are never committed;
- `db/` — MySQL schema/migrations;
- `public/` — Apache/shared-hosting routing templates;
- `tests/` — HOSTING contract/security checks.

## Configuration

`config/config.example.php` is a non-secret template. A real installation will use `config/config.local.php`, which is ignored by Git and must stay outside public reach in the final Timeweb package.

For CI/local automation the same database settings may be supplied through:

```text
ASTREA_HOSTING_DB_DSN
ASTREA_HOSTING_DB_USER
ASTREA_HOSTING_DB_PASSWORD
```

No production credentials belong in Git.

## Database

`db/001_initial.sql` creates the H2 schema and is safe to apply again without overwriting existing predefined-page content.

Tables:

- `pages` — six immutable/predefined public page keys;
- `news` — lodge news;
- `materials` — unified `book | video | audio | article` collection;
- `events` — public calendar dates;
- `editor_users` — account storage reserved for H3, with no seeded credentials;
- `hosting_schema_migrations` — HOSTING schema version marker.

The predefined pages are seeded unpublished with the same keys used by the FULL edition.

## Public API — H2

The PHP API is read-only in H2 and returns only rows explicitly marked published.

Existing shared-frontend-compatible routes:

```text
GET /api/health
GET /api/v1/health
GET /api/v1/pages/{key}
GET /api/v1/news
GET /api/v1/news/{slug}
GET /api/v1/videos
GET /api/v1/videos/{id}
```

HOSTING-specific routes for the agreed MVP:

```text
GET /api/v1/materials
GET /api/v1/materials/{slug}
GET /api/v1/events
```

Lists accept bounded `limit`/`offset`. Materials may be filtered with `?type=book|video|audio|article`. Events accept optional ISO date bounds such as `?from=2026-09-01&to=2027-01-31`.

The `/videos` contract is derived from published `video` materials and accepts only canonical HTTPS RuTube URLs matching the already accepted FULL-edition provider model. Arbitrary iframe/HTML is never exposed.

No public or editor write endpoint exists yet. Candidate submission paths remain absent and return `404`.

## Expected final document-root shape

H5 will build the upload-ready package. Conceptually the hosting document root will contain:

```text
index.html
assets/
brand/
media/
api/
editor/        # H3
.htaccess
```

Private configuration/database bootstrap sources are not to be exposed as public static files.
