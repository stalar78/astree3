# Project Blueprint: Astrea

Current stage: Stage 4.4A admin authentication accepted; Stage 4.4B candidate administration next.

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

## Accepted Stage 4.1 Backend Foundation

The production backend foundation is implemented in `backend/` with:
- FastAPI application factory and `/api/v1/health`;
- environment-based settings through `pydantic-settings`;
- PostgreSQL DSN validation and explicit psycopg 3 URL normalization;
- SQLAlchemy 2.x engine/session foundation;
- Alembic metadata/configuration;
- pytest backend tests;
- Ruff quality gate.

Stage 4.1 contains no candidate intake, uploads, email, admin authentication or content CRUD.

## Accepted Stage 4.2 Public Content Domain

The backend now includes structured public content for:
- predefined editable pages;
- news posts;
- external videos.

Accepted behavior:
- PostgreSQL models and one Alembic migration for `pages`, `news_posts` and `videos`;
- published-only public read endpoints under `/api/v1`;
- stable, model-level validated page keys and news slugs;
- bounded pagination and deterministic ordering for news/video lists;
- strict HTTPS RuTube validation with canonical source URLs and derived embed URLs;
- no arbitrary iframe/embed HTML;
- RuTube provider consistency enforced at model and database-constraint level;
- no public write endpoints, admin CRUD, candidate models, email models or frontend integration in this slice.

Stage 4.2 was accepted after corrective validation hardening and migration regression review.

## Accepted Stage 4.3 Candidate Intake and Private Media

The backend now includes the guarded candidate-intake foundation:
- `candidate_applications`, `application_consents` and `email_outbox` persistence;
- exact Saint Petersburg acknowledgement contract;
- three required consent records with server-controlled document versions;
- private candidate-photo decoding, validation, EXIF-orientation handling, metadata stripping and JPEG normalization;
- private generated storage keys with traversal-safe filesystem storage and cleanup support;
- one transactional intake aggregate: candidate + three consents + one pending outbox row;
- rollback and private-photo cleanup for all pre-commit failures after photo storage;
- disabled-by-default public multipart candidate POST route;
- authoritative server-side field validation;
- strict explicit consent parsing;
- honeypot and process-local MVP rate limiting;
- bounded upload reading before Pillow processing;
- generic candidate validation/error responses without PII echo;
- no public candidate GET/photo route;
- no email sending yet.

`CANDIDATE_INTAKE_ENABLED` defaults to `false`. When disabled, the candidate POST route is not registered and is absent from OpenAPI. Enabling intake requires all three server-controlled legal version identifiers.

Stage 4.3 was accepted after dedicated persistence, image-safety, public-ingress and transactional-cleanup hardening. Final reported quality gate: 123 pytest tests passed and Ruff passed.

The feature remains intentionally inactive until approved legal documents, frontend integration and deployment/security review are complete.

## Accepted Stage 4.4A Admin Authentication

The backend now includes the closed administrator authentication boundary:
- `admin_users` and `admin_sessions` persistence with migration `20260822_0003`;
- Argon2id password hashing and verification;
- explicit initial-admin bootstrap only, with no automatic startup creation;
- opaque server-issued session and CSRF tokens with only SHA-256 digests stored in PostgreSQL;
- `POST /api/v1/admin/auth/login`, `POST /api/v1/admin/auth/logout` and `GET /api/v1/admin/auth/me`;
- server-side session lookup and inactive/expired-session rejection;
- `HttpOnly`, `SameSite=Strict` session cookie, `Secure` outside local/dev/test;
- independent browser-readable CSRF cookie with `X-CSRF-Token` validation for logout and future state-changing admin routes;
- fixed session TTL and no sliding extension;
- process-local login rate limiting keyed by direct client host, without IP persistence or direct trust of `X-Forwarded-For`;
- dummy Argon2 verification on missing/inactive users to reduce account-enumeration timing differences;
- password rehash support in the same transaction as new session creation;
- generic validation/auth/database failures without password/session/CSRF echo;
- no JWT, no auth token in `localStorage`, no admin registration and no complex RBAC.

Stage 4.4A was accepted after separate persistence/cryptography/bootstrap and HTTP session/CSRF reviews. Final reported backend quality gate from `backend/`: 165 pytest tests passed and Ruff passed.

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

1. Stage 4.1 - accepted: FastAPI backend foundation, settings, PostgreSQL/SQLAlchemy integration, Alembic, health endpoint and backend tests.
2. Stage 4.2 - accepted: structured public content persistence/read API for pages, news and approved RuTube videos.
3. Stage 4.3 - accepted: guarded candidate intake persistence, private photo pipeline, transactional consent/outbox aggregate and disabled-by-default public ingress.
4. Stage 4.4A - accepted: closed admin identity/bootstrap, Argon2id passwords, server-side sessions, secure cookies, CSRF protection and auth dependencies.
5. Stage 4.4B - next: authenticated candidate list/detail/status workflow and private-photo access.
6. Stage 4.4C - authenticated administration for news, video and approved editable page content.
7. Stage 4.4D - persistent email-outbox worker/retry delivery.
8. Before candidate intake activation: approve legal documents/version identifiers, integrate the frontend form, and complete deployment request-body/client-IP security configuration.
