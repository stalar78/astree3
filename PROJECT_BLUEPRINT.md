# Project Blueprint: Astrea

Current stage: Stage 4.4D1 persistent email outbox state machine accepted; Stage 4.4D2 SMTP delivery and worker execution next.

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

## Accepted Stage 4.4B1 Candidate Administration Backend

The backend now includes the protected candidate-administration API:
- operational candidate statuses `new`, `in_review`, `contacted`, `closed`, `archived`;
- migration `20260822_0004` with required/defaulted/indexed/constrained candidate status;
- authenticated candidate list with bounded pagination, deterministic newest-first ordering and optional status filtering;
- summary-only list responses and a separate authenticated detail boundary for full review fields and immutable consent evidence;
- authenticated private-photo access addressed only through candidate application ID;
- private storage-key validation, root confinement, regular-file checks and final-symlink rejection where the platform supports it;
- server-side JPEG media and recorded-size integrity checks before photo delivery;
- sensitive admin responses marked `private, no-store`, with `nosniff` on photo responses;
- CSRF-protected candidate status updates with generic persistence failures and rollback;
- no candidate deletion/editing/export/bulk operations, no public candidate read/photo aliases and no exposure of private storage keys or filesystem paths.

Stage 4.4B1 was accepted after candidate-PII/private-media/security review. Final reported backend quality gate from `backend/`: 194 pytest tests passed, 1 platform-dependent symlink test skipped, and Ruff passed.

## Accepted Stage 4.4B2 Candidate Administration UI

The production frontend now includes a protected candidate-administration interface:
- `/admin/login` and a separate protected `/admin` route tree outside the public `PageShell`;
- session verification through `GET /api/v1/admin/auth/me` before protected PII is rendered;
- no JWT, no `localStorage`/`sessionStorage` auth, and no JavaScript access to the `HttpOnly` session cookie;
- candidate list with status filtering, `limit=20` offset pagination and operational URL state limited to `status`/`offset`;
- candidate detail with read-only PII and human-readable immutable consent evidence;
- private candidate photos fetched only through the authenticated candidate-photo API and rendered via revocable in-memory Blob URLs;
- explicit status updates and logout using the accepted readable CSRF cookie plus `X-CSRF-Token` header;
- distinct handling of invalid sessions (`401`), CSRF failures (`403`) and temporary backend/network failures without false success states;
- retry controls for temporary session/list failures;
- generic frontend error messages without raw server/proxy text exposure;
- development-only Vite `/api` proxy while production requests remain same-origin relative `/api/v1` calls;
- no candidate deletion/editing/export/bulk operations and no public admin navigation.

Stage 4.4B2 was accepted after corrective pagination, CSRF/logout semantics, private-photo, PII/storage and error-boundary review. Final reported frontend quality gate from `frontend/`: `npm run typecheck`, `npm run lint` and `npm run build` all passed.

## Accepted Stage 4.4C1 Content Administration Backend

The backend includes authenticated administration of the accepted Stage 4.2 content models under `/api/v1/admin/content`:
- news list/detail/create/update/delete, with bounded pagination, optional `published` filtering and deterministic admin ordering;
- server-managed publication timestamps where first publish sets UTC time and later unpublish/republish preserves the original timestamp;
- duplicate news slugs mapped safely to `409` with rollback;
- optional news image references restricted to safe HTTPS absolute URLs or root-relative same-origin paths, with no network fetching or storage side effects;
- video list/detail/create/update/delete using the existing strict RuTube validator, canonical source URLs and server-derived provider/embed URLs;
- no arbitrary iframe HTML, arbitrary provider input or client-controlled publication timestamps;
- predefined page administration limited to list/detail/update of existing rows, with immutable keys and no page create/delete route;
- accepted Stage 4.4A session authentication for reads and CSRF protection for every content write;
- strict request schemas, scoped validation privacy and `private, no-store` admin response caching;
- generic database failure handling with rollback and no SQL/DSN/constraint leakage;
- mutation responses finalized as `flush -> refresh -> commit -> serialize`, with regression tests proving no database access after successful commit and rollback-safe pre-commit refresh failures;
- existing public Stage 4.2 APIs remain published-only and operate on the same PostgreSQL rows;
- no migration `0005`, no new content/revision/audit tables and no schema expansion.

Stage 4.4C1 was accepted after dedicated draft/public-boundary, page-identity, RuTube-validation, CSRF, validation-privacy and post-commit transaction review. Final reported backend quality gate from `backend/`: 231 pytest tests passed, 1 skipped, and Ruff passed.

## Accepted Stage 4.4C2 Content Administration UI

The production frontend now includes protected content administration inside the accepted `/admin` shell:
- navigation for Candidates, News, Video and Pages with protected routes outside the public `PageShell`;
- news list/create/edit/delete and publish/unpublish controls with `limit=20` pagination and `published` filtering;
- canonical list URL state limited to non-content `published`/`offset` parameters, with invalid or unknown parameters removed;
- safe duplicate news-slug handling that keeps current form values editable;
- explicit two-step news/video deletion without optimistic removal or automatic mutation retry;
- RuTube video create/edit limited to title, description, canonical RuTube source URL and publication state, with provider/embed state server-owned and no automatic iframe preview;
- predefined page list/edit limited to existing immutable page keys and title/content/publication state, with no create/delete/page-builder surface;
- same-origin session-cookie authentication and existing readable CSRF cookie plus `X-CSRF-Token` for every write;
- `401` redirects to login, while write `403` stays on the current editor and shows the accepted session-security message;
- temporary/network GET failures provide explicit retry, while mutation failures preserve in-memory form state and require explicit user retry;
- news image references accept HTTPS absolute or root-relative same-origin paths without preview, network fetch or upload;
- no raw backend error detail rendered to the user;
- unpublished editorial drafts remain only in React component memory: no browser storage, URL content payloads, cookies, console logging or autosave;
- public frontend behavior and public content APIs remain unchanged;
- no new frontend dependencies.

Stage 4.4C2 was accepted after corrective review of mutation-error form visibility, temporary detail-load retry, root-relative image URL compatibility and browser URL-state canonicalization. Final reported frontend quality gate from `frontend/`: `npm run typecheck`, `npm run lint` and `npm run build` all passed.

## Accepted Stage 4.4D1 Persistent Email Outbox State Machine

The backend now includes the durable persistence contract required before real email delivery:
- migration `20260823_0005` adds only `processing_started_at` and `next_attempt_at` to the existing `email_outbox` table and preserves the accepted eight-table schema surface;
- already-processing rows are backfilled before the processing timestamp check constraint is applied;
- ORM metadata and migration share the same composite claim index `ix_email_outbox_status_next_attempt_id(status, next_attempt_at, id)`;
- environment-backed policy controls batch size, max attempts, retry base/max delay and processing timeout with safe defaults and validation;
- only due `pending` rows are claimed, oldest first, with bounded batches and PostgreSQL `FOR UPDATE SKIP LOCKED`;
- claiming increments `attempts`, marks `processing`, records `processing_started_at`, clears retry scheduling and commits before future external delivery;
- immutable claim descriptors contain only outbox/application/event identity and attempt number, not candidate PII;
- success/failure transitions are atomically guarded by `id + status=processing + attempts=attempt_number`, so a stale worker cannot overwrite a newer generation;
- retryable failures below max attempts return to `pending` with deterministic capped exponential backoff, while permanent/exhausted failures become terminal `failed`;
- stale `processing` rows are recovered in bounded batches, requeued below max attempts or terminally failed at max attempts;
- `last_error` accepts only closed machine-safe codes such as temporary/permanent/unexpected delivery failure and processing timeout; raw exception text, SMTP details, PII and secrets are not persisted there;
- candidate intake remains the source of new outbox work and still creates exactly one `pending`, attempts=0 outbox entry in the same transaction as candidate/consent persistence;
- no SMTP transport, email rendering, worker CLI, daemon loop or network delivery exists in D1;
- delivery semantics are intentionally at-least-once around future SMTP: a provider may accept a message before a process dies and before `sent` is committed, so duplicate retry remains possible rather than being hidden behind a false exactly-once claim.

Stage 4.4D1 was accepted after dedicated schema/metadata alignment, PostgreSQL claim-query, stale-generation, backoff-cap, stale-recovery, failure-privacy and DB-failure review. Final reported backend quality gate from `backend/`: 247 pytest tests passed, 1 skipped, 14 pre-existing Starlette `TestClient` deprecation warnings remained, and Ruff passed.

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
5. Stage 4.4B - accepted: authenticated candidate list/detail/status/private-photo API plus protected candidate admin UI.
6. Stage 4.4C - accepted: authenticated backend and protected frontend administration for news, RuTube video and predefined editable page content.
7. Stage 4.4D1 - accepted: persistent outbox claim/retry/recovery state machine with PostgreSQL concurrency protection and safe failure codes.
8. Stage 4.4D2 - next: SMTP transport, structured notification rendering and explicit worker execution using the accepted D1 state machine.
9. Before candidate intake activation: approve legal documents/version identifiers, integrate the public frontend form, and complete deployment request-body/client-IP security configuration.
