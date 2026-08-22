# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 4.3 candidate intake and private media accepted; Stage 4.4 admin and operations is next.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. The production public frontend lives in `frontend/` and was accepted after visual and technical review. The backend foundation, public content domain and guarded candidate-intake pipeline live in `backend/`.

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

- `frontend/` - accepted production public frontend; candidate submission UI remains intentionally inactive pending legal approval and integration
- `backend/` - accepted FastAPI/PostgreSQL foundation, Stage 4.2 public content API, and Stage 4.3 guarded candidate-intake/private-photo pipeline
- `infra/` - deployment/runtime configuration target

Candidate intake is disabled by default. `CANDIDATE_INTAKE_ENABLED` must remain false until the approved privacy/consent documents, server-controlled legal version identifiers, frontend wiring and deployment/security review are complete.

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
