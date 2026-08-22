# Project Blueprint: Astrea

Current stage: Stage 3 public frontend accepted; Stage 4 backend foundation next.

## Purpose

Build a new official public website for Astrea with manageable content and a secure candidate application workflow.

## Users

Primary public users:
- Visitors interested in the lodge
- Potential candidates

Internal user:
- Site administrator

## Success Criterion

A production-ready site passes the approved acceptance criteria, including a complete end-to-end candidate application: form -> validation -> secure persistence -> admin availability -> email notification.

## Current MVP Scope

Public:
- Home
- About / Saint Petersburg lodges
- Goals and principles
- Join / candidate application
- FAQ
- News
- Video
- Contacts
- Privacy/legal pages

Admin:
- Authentication
- Dashboard
- News management
- Video management
- Editable allowed page content
- Candidate application list/details/statuses

Candidate application:
- Form
- Photo upload
- Consent checkboxes
- Server-side validation
- Anti-spam protection
- Database persistence
- Private photo storage
- Structured email notification

## Out of Scope for Initial Version

- Member personal accounts
- Public user registration
- Internal social network
- CRM
- Telegram bot
- Mobile application
- Own video hosting
- Streaming from VPS
- Payments
- Multilingual version
- Complex admin role system
- Bulk email campaigns
- External CRM integrations
- AI features

## Architecture Baseline

Detailed architecture: `.architecture/ARCHITECTURE.md`.

High-level runtime:

```text
Browser
 -> Nginx / HTTPS
     -> React frontend
     -> /api/v1 -> FastAPI
                    -> PostgreSQL
                    -> public editorial media
                    -> private candidate media
                    -> persistent email outbox

Email worker -> SMTP / email provider
Video pages -> approved external provider URLs, primarily RuTube
```

Key decisions:
- PostgreSQL is the source of truth for candidate applications.
- Candidate data is persisted before email delivery is attempted.
- Candidate photos are private and never served as an open static directory.
- Email delivery uses a persistent outbox and retryable worker.
- Admin authentication uses secure server-side/session-cookie semantics; no privileged token storage in browser localStorage.
- External video embeds are provider/domain allowlisted.
- MVP stays a modular monolith; no Redis/Celery/microservices unless later justified.

## Design Direction

Detailed design baseline: `docs/DESIGN_SYSTEM.md`.

Approved Stage 2 visual freeze and implementation handoff: `docs/STAGE_2_DESIGN_FREEZE.md`.

Brand source: client Jubilee Repository, especially pages 4-5.

Official palette references:
- Pantone 485 C - red accent
- Pantone Cool Gray 6 C
- Pantone Cool Gray 10 C
- Pantone Process Black C
- White

Working screen approximations are defined in `docs/DESIGN_SYSTEM.md`; Pantone remains the brand source of truth.

Approved visual direction:
- monumental and institutional;
- historical/editorial rather than SaaS or commercial landing-page design;
- classical and restrained;
- large margins and narrow text columns;
- dark official header/internal heroes;
- official client-supplied heraldry, standard and seal;
- no generic occult styling;
- no excessive animation;
- no invented Masonic symbols or stock imagery.

The approved Lovable prototype is the visual reference only. Production architecture remains the repository architecture baseline.

## Accepted Stage 3 Frontend

The production public frontend is implemented in `frontend/` with:
- React + TypeScript + Vite + Tailwind;
- React Router;
- all approved public routes;
- accepted ceremonial header, centered home hero and monumental footer;
- full institutional homepage sequence;
- distinct internal page compositions;
- static candidate form UI only, with no submission or persistence yet;
- exact approved public brand assets;
- route-specific metadata.

Stage 3 was merged only after build, lint, typecheck and visual-structure review.

## Security

Main security risk: candidate forms contain personal data and photos.

Security requirements:
- HTTPS
- Private candidate data
- Non-public candidate photos
- Authenticated admin
- Secrets only through environment variables
- Backup policy
- Server-side validation
- Upload validation and image normalization
- Anti-spam/rate limiting
- Persistent consent records
- No production write access for agents without explicit approval

The `religion` field remains disabled until the client approves the legal wording and processing basis for special-category personal data.

## Current Next Steps

Stage 4 is split into small reviewed slices; see `.plans/STAGE_4_BACKEND_PLAN.md`.

1. Stage 4.1 - create the FastAPI backend foundation, settings, PostgreSQL/SQLAlchemy integration, Alembic migrations, health endpoint and backend tests.
2. Stage 4.2 - implement structured public content models/API for pages, news and external videos.
3. Stage 4.3 - implement the high-risk candidate intake transaction: authoritative validation, consent persistence, private image handling and persistent email outbox.
4. Stage 4.4 - implement closed admin authentication and candidate/content administration.
5. Integrate the accepted frontend with backend APIs only after each backend slice passes review.
