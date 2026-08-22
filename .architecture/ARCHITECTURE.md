# Astrea Architecture

Status: Stage 1 baseline. This document defines the implementation direction for the MVP.

## 1. Repository layout

Planned runtime structure:

```text
frontend/   React + TypeScript + Vite + Tailwind
backend/    FastAPI application, API, auth, persistence, email worker
infra/      Docker Compose and deployment configuration
docs/       product/design/operations documentation
```

`_ref/` remains local-only client source material and is never used as a runtime directory.

## 2. Runtime topology

```text
Browser
  -> Nginx / HTTPS
      -> static React build
      -> /api/* -> FastAPI
                    -> PostgreSQL
                    -> private application-photo storage
                    -> public editorial-image storage
                    -> email outbox

Email worker
  -> PostgreSQL outbox
  -> SMTP / email provider

Video pages
  -> approved external provider URLs, primarily RuTube
```

The first release does not require Redis, Celery, Kubernetes or separate microservices.

## 3. Frontend

- React + TypeScript + Vite + Tailwind CSS.
- React Router for public and admin routes.
- Public page layouts and admin layouts are separate shells.
- Public pages use fixed design components; admin users edit content, not arbitrary layout code.
- Candidate form performs client validation for UX, but server validation remains authoritative.
- No secrets or privileged logic in the frontend.

SEO baseline:
- route-specific title/description/canonical/Open Graph data;
- semantic H1-H3 structure;
- sitemap.xml and robots.txt;
- news routes receive stable human-readable slugs.

If SPA indexing proves insufficient during pre-release verification, public-route prerendering may be added without changing the backend contract.

## 4. Backend

FastAPI owns:
- public content API;
- candidate application submission;
- upload validation and image normalization;
- admin authentication and authorization;
- news/video/page management;
- application review/status changes;
- SEO-supporting data;
- email outbox creation.

API namespace: `/api/v1`.

## 5. Persistence

PostgreSQL is the source of truth.

Initial entities:
- `admin_users`
- `pages`
- `news_posts`
- `videos`
- `candidate_applications`
- `application_consents`
- `email_outbox`

Candidate applications are persisted before any email notification is attempted.

The email is a notification channel, not application storage.

## 6. Candidate application flow

```text
submit form
 -> client validation
 -> FastAPI multipart request
 -> server field validation
 -> anti-spam/rate-limit checks
 -> image validation + normalization
 -> DB transaction: application + consent records + email_outbox
 -> success response
 -> worker attempts email delivery
```

A failed email must not roll back or lose an accepted application.

Consent records should capture at minimum consent type, accepted timestamp and document/policy version.

The `religion` field remains feature-disabled until the client approves the legal wording and processing basis for special-category personal data.

## 7. File storage

Two storage classes must remain separate:

### Public editorial media
News/site images intended for visitors. They may be exposed through controlled public URLs.

### Private candidate media
Candidate photographs are stored outside the public web root.

Private photos:
- use generated identifiers, not original file names;
- are never served by Nginx as a public directory;
- are returned only through an authenticated admin endpoint;
- have upload size/dimension limits;
- are validated by actual image decoding, not extension alone;
- are normalized/re-encoded to strip unnecessary metadata such as EXIF.

The storage abstraction should allow later migration to S3-compatible storage without changing application-domain logic.

## 8. Admin authentication

MVP assumes a small closed administrator group and no public registration.

Preferred model:
- password hash using a modern password-hashing algorithm;
- server-issued session cookie;
- `HttpOnly`, `Secure` and appropriate `SameSite` attributes in production;
- no auth tokens in `localStorage`;
- CSRF protection for state-changing authenticated operations where required by the chosen session implementation.

## 9. Video handling

The application stores metadata and approved external URLs, not video files.

For embeds:
- allowlist supported providers/domains;
- derive embed URLs rather than accepting arbitrary iframe HTML;
- reject unsupported or malformed URLs.

RuTube is the primary provider for the first release.

## 10. Content model

News is structured content with draft/published states and stable slugs.

Static information pages use constrained editable fields/blocks. The admin panel must not become a free-form page builder capable of breaking the approved layout.

## 11. Email delivery

Use a persistent outbox table instead of relying only on an in-process background task.

Each queued message records status, attempts, last error and timestamps. A lightweight worker can retry failed sends without requiring Redis/Celery for the MVP.

## 12. Deployment

Production baseline:
- Linux VPS
- Docker Compose
- Nginx
- TLS/SSL
- PostgreSQL
- frontend build
- FastAPI service
- email worker
- persistent volumes for database/private uploads as appropriate

Backups must include PostgreSQL and private candidate-media storage.

## 13. Security boundaries

High-risk surfaces:
- candidate form;
- image upload;
- admin authentication;
- private application/photo access;
- content rendering;
- external video embedding.

Required controls include server validation, rate limiting, honeypot/anti-bot checks, safe rendering/sanitization, upload normalization, authenticated private-media access and secret management through environment variables.

## 14. Deliberately excluded complexity

Do not introduce in the MVP without a demonstrated need:
- microservices;
- Redis;
- Celery;
- message brokers;
- Kubernetes;
- public accounts;
- complex RBAC;
- custom video hosting.
