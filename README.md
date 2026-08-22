# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 4.1 backend foundation accepted; Stage 4.2 public content domain is next.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. The production public frontend lives in `frontend/` and was accepted after visual and technical review. The backend foundation now lives in `backend/`.

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

- `frontend/` - accepted production public frontend
- `backend/` - accepted Stage 4.1 FastAPI/PostgreSQL foundation
- `infra/` - deployment/runtime configuration target

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
