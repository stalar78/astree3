# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 4.4C content administration accepted; Stage 4.4D email outbox operations is next.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. The production public frontend lives in `frontend/` and was accepted after visual and technical review. The backend foundation, public content domain, guarded candidate-intake pipeline, closed admin authentication, candidate administration API and content administration API live in `backend/`; protected candidate and content administration interfaces live in the production frontend.

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

- `frontend/` - accepted production public frontend plus protected candidate administration and Stage 4.4C2 protected content administration UI; public candidate submission remains intentionally inactive pending legal approval and integration
- `backend/` - accepted FastAPI/PostgreSQL foundation, Stage 4.2 public content API, Stage 4.3 guarded candidate-intake/private-photo pipeline, Stage 4.4A closed server-side admin authentication, Stage 4.4B1 authenticated candidate administration/private-photo API, and Stage 4.4C1 authenticated content administration API
- `infra/` - deployment/runtime configuration target

Admin authentication uses Argon2id passwords, explicit initial-admin bootstrap, server-side opaque sessions, `HttpOnly` session cookies, separate CSRF tokens and process-local login rate limiting. There is no public/admin registration, JWT or browser `localStorage` authentication.

Candidate administration is available through authenticated `/api/v1/admin/candidates` routes and the protected `/admin` frontend. Candidate photo storage keys and private filesystem paths are not exposed, private photos are fetched only through the authenticated admin endpoint, and status mutations/logout use the accepted CSRF flow.

Content administration is available through authenticated `/api/v1/admin/content` routes and protected `/admin/news`, `/admin/videos` and `/admin/pages` frontend routes. News and RuTube videos support protected create/read/update/delete operations, while predefined pages support only authenticated list/detail/update; page identities cannot be created, deleted or renamed. Draft content remains excluded from the public Stage 4.2 endpoints, write `403` errors remain on-page, and unpublished editorial state is not persisted in browser storage or URLs.

Candidate intake is disabled by default. `CANDIDATE_INTAKE_ENABLED` must remain false until the approved privacy/consent documents, server-controlled legal version identifiers, public frontend wiring and deployment/security review are complete.

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
