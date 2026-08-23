# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 4 backend implementation and guarded public candidate-form integration are accepted. Candidate intake activation remains deferred pending legal and deployment/security prerequisites.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. The production public frontend lives in `frontend/` and was accepted after visual and technical review. The backend foundation, public content domain, guarded candidate-intake pipeline, closed admin authentication, candidate administration API, content administration API, persistent email-outbox state machine and SMTP worker execution live in `backend/`; protected candidate/content administration and the guarded public candidate form live in the production frontend.

## Application Scope

- Public informational website
- News section
- External video section, primarily RuTube URLs
- Candidate application form with photo upload
- Candidate application persistence
- Formatted email notifications
- Protected administration panel
- Editable content
- SEO
- Responsive desktop/tablet/mobile UI

## Stack

Frontend: React + TypeScript + Vite + Tailwind CSS

Backend: Python + FastAPI + SQLAlchemy + Alembic

Database: PostgreSQL via psycopg 3

Infrastructure: Linux VPS + Docker Compose + Nginx + SSL

## Architecture and Design

- Application architecture: `.architecture/ARCHITECTURE.md`
- Design system: `docs/DESIGN_SYSTEM.md`
- Approved Stage 2 visual freeze: `docs/STAGE_2_DESIGN_FREEZE.md`
- Stage 4 backend plan: `.plans/STAGE_4_BACKEND_PLAN.md`
- Requirements: `docs/REQUIREMENTS.md`
- Project blueprint: `PROJECT_BLUEPRINT.md`

## Current Implementation

- `frontend/` - accepted production public frontend, guarded candidate-application form integration, protected candidate administration and Stage 4.4C2 protected content administration UI; public candidate submission remains intentionally disabled by default through `VITE_CANDIDATE_FORM_ENABLED=false`
- `backend/` - accepted FastAPI/PostgreSQL foundation, Stage 4.2 public content API, Stage 4.3 guarded candidate-intake/private-photo pipeline, Stage 4.4A closed server-side admin authentication, Stage 4.4B1 authenticated candidate administration/private-photo API, Stage 4.4C1 authenticated content administration API, Stage 4.4D1 persistent outbox state machine, and Stage 4.4D2 SMTP notification rendering/transport plus one-shot email-worker execution
- `infra/` - deployment/runtime configuration target

Admin authentication uses Argon2id passwords, explicit initial-admin bootstrap, server-side opaque sessions, `HttpOnly` session cookies, separate CSRF tokens and process-local login rate limiting. There is no public/admin registration, JWT or browser `localStorage` authentication.

Candidate administration is available through authenticated `/api/v1/admin/candidates` routes and the protected `/admin` frontend. Candidate photo storage keys and private filesystem paths are not exposed, private photos are fetched only through the authenticated admin endpoint, and status mutations/logout use the accepted CSRF flow.

Content administration is available through authenticated `/api/v1/admin/content` routes and protected `/admin/news`, `/admin/videos` and `/admin/pages` frontend routes. News and RuTube videos support protected create/read/update/delete operations, while predefined pages support only authenticated list/detail/update; page identities cannot be created, deleted or renamed. Draft content remains excluded from the public Stage 4.2 endpoints, write `403` errors remain on-page, and unpublished editorial state is not persisted in browser storage or URLs.

The public `/vstuplenie` candidate form now matches the accepted multipart backend contract, including photo upload, honeypot, three required consent fields and the exact Saint Petersburg acknowledgement. It uses uncontrolled form controls and same-origin `FormData`, does not persist candidate PII in browser storage/URLs/cookies, and exposes only generic status-mapped public errors. The separate frontend gate is fail-closed and defaults to disabled.

Email delivery now uses the existing persistent `email_outbox` state machine plus a finite `process-email-outbox` worker command. The worker validates SMTP configuration only at execution time, recovers stale work, claims a bounded committed batch, builds an immutable candidate snapshot in a short database session, renders UTF-8 plain/HTML administrator notifications, performs verified STARTTLS/SMTP-SSL delivery with no database transaction open, and records success/failure through the accepted D1 guarded transitions. Candidate photos are not attached to email; the notification links only to the authenticated admin candidate page. The delivery model remains intentionally at-least-once around the SMTP-accepted/DB-not-yet-marked-sent crash window.

Candidate intake is disabled by default at both layers: `VITE_CANDIDATE_FORM_ENABLED=false` keeps the public form non-operational, while `CANDIDATE_INTAKE_ENABLED=false` keeps the backend route unregistered. Both must remain disabled until approved privacy/consent documents and server-controlled legal version identifiers are available and deployment/security review is complete. Production scheduling/service wiring and real SMTP credentials/connectivity are deployment concerns and are not hidden inside the FastAPI process.

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
