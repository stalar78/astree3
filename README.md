# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 2 visual system approved; Stage 3 public frontend implementation is next.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. Production application code is being introduced only after the visual system has been accepted.

## Planned Application

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

## Planned Stack

Frontend: React + TypeScript + Vite + Tailwind CSS

Backend: Python + FastAPI

Database: PostgreSQL

Infrastructure: Linux VPS + Docker Compose + Nginx + SSL

## Architecture and Design

- Application architecture: `.architecture/ARCHITECTURE.md`
- Design system: `docs/DESIGN_SYSTEM.md`
- Approved Stage 2 visual freeze: `docs/STAGE_2_DESIGN_FREEZE.md`
- Requirements: `docs/REQUIREMENTS.md`
- Project blueprint: `PROJECT_BLUEPRINT.md`

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
