# Astrea HOSTING Edition

This directory contains the shared-hosting backend/package layer for the approved Astrea HOSTING edition.

Current implementation stage: **H1 foundation only**. It is not yet production-deployable.

## Runtime target

- existing shared React frontend built with `npm run build:hosting`;
- Apache-compatible shared hosting;
- PHP backend under `/api`;
- MySQL persistence added in H2;
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

- `api/` — PHP API entry and later controllers;
- `config/` — safe templates only; production/local credentials are never committed;
- `db/` — MySQL schema/migrations from H2;
- `public/` — Apache/shared-hosting routing templates;
- `tests/` — HOSTING contract/security checks added incrementally.

## Configuration

`config/config.example.php` is a non-secret template. A real installation will use `config/config.local.php`, which is ignored by Git and must stay outside public reach in the final Timeweb package.

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

## H1 health endpoint

The PHP skeleton currently exposes only a harmless readiness endpoint:

```text
GET /api/health
GET /api/v1/health
```

All other API paths return `404`, including candidate submission paths.
