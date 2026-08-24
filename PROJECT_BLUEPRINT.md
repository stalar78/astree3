# Project Blueprint: Astrea

Current stage: the Stage 4 application foundation and administration flows, protected Admin Dashboard, guarded public candidate-form integration, Stage 5.1 production-like runtime, Stage 5.2 deployment security hardening, Stage 5.3A backup/restore foundation, Stage 5.3B operations/retention/scheduling, Stage 5.3C SMTP readiness implementation, CI Foundation and the PostgreSQL Integration Gate are accepted. Public News, Video and predefined managed-page integrations are accepted. Repository governance now uses `main` as the default protected branch with the accepted CI checks required by an active ruleset. Controlled candidate-workflow acceptance is partially complete, but public candidate intake remains disabled pending approved legal texts/version identifiers, live SMTP-provider verification and production infrastructure prerequisites.

## Purpose

Build a new official public website for Astrea with manageable editorial content and a secure candidate application workflow.

## Users

Primary public users:
- Visitors interested in the lodge
- Potential candidates

Internal user:
- Site administrator

## Success Criterion

A production-ready site passes the approved acceptance criteria, including a complete end-to-end candidate application: form -> validation -> secure persistence -> admin availability -> email notification.

The public site must also expose only approved/published editorial content and keep candidate data, private photos, credentials and unpublished material outside public access.

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
- Dashboard / overview
- Candidate application list/details/statuses/private photo
- News management
- Video management
- Editable predefined page content

Candidate application:
- Form
- Photo upload
- Consent checkboxes
- Server-side validation
- Anti-spam protection
- Database persistence
- Private photo storage
- Persistent email outbox
- Structured administrator email notification

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

Finite email worker -> SMTP / email provider
Video pages -> approved external provider URLs, primarily RuTube
```

Key decisions:
- PostgreSQL is the source of truth for candidate applications and managed content.
- Candidate data is persisted before email delivery is attempted.
- Candidate photos are private and never served as an open static directory.
- Email delivery uses a persistent outbox and finite retryable worker execution.
- Admin authentication uses server-side sessions and cookies; no privileged token storage in browser `localStorage`.
- External video embeds are provider/domain allowlisted and server-derived.
- Predefined managed pages have immutable keys and no public/admin page-creation surface.
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

The production public frontend is implemented in `frontend/` with React, TypeScript, Vite, Tailwind and React Router. The accepted visual system, public routes, institutional homepage, internal page compositions, official client-supplied brand assets and route-specific metadata are implemented.

Stage 3 originally contained only the static candidate-form UI. Candidate submission was integrated later as a separately guarded slice and remains disabled by default.

## Accepted Stage 4.1 Backend Foundation

The backend foundation in `backend/` includes:
- FastAPI application factory and `/api/v1/health`;
- environment-based settings through `pydantic-settings`;
- PostgreSQL/psycopg 3 DSN validation;
- SQLAlchemy 2.x engine/session foundation;
- Alembic metadata/configuration;
- pytest backend tests;
- Ruff quality gate.

## Accepted Stage 4.2 Public Content Domain

Structured content persistence and published-only public read APIs exist for:
- predefined editable pages;
- news posts;
- external videos.

Accepted security/contract properties include stable validated page keys/news slugs, bounded deterministic lists, strict HTTPS RuTube validation, canonical source URLs, server-derived embed URLs and no arbitrary iframe/embed HTML.

## Accepted Stage 4.3 Candidate Intake and Private Media

The guarded candidate-intake foundation includes:
- `candidate_applications`, `application_consents` and `email_outbox` persistence;
- three required server-versioned consent records;
- exact Saint Petersburg acknowledgement contract;
- private image decoding, validation, EXIF-orientation handling, metadata stripping and JPEG normalization;
- generated traversal-safe private storage keys;
- transactional candidate + consents + pending outbox creation;
- rollback/private-photo cleanup on pre-commit failure;
- disabled-by-default multipart candidate POST;
- authoritative server-side validation;
- strict consent parsing, honeypot and MVP rate limiting;
- bounded upload reading and generic non-PII public errors.

`CANDIDATE_INTAKE_ENABLED` defaults to `false`. When disabled, the candidate POST route is not registered and is absent from OpenAPI.

## Accepted Stage 4.4A Admin Authentication

The closed administrator boundary includes:
- `admin_users` and `admin_sessions` persistence;
- Argon2id password hashing;
- explicit initial-admin bootstrap only;
- opaque server-side sessions;
- `HttpOnly`, `SameSite=Strict` session cookie and separate CSRF cookie/header flow;
- fixed session TTL;
- login rate limiting;
- generic auth/database failures;
- no JWT, public registration or browser token storage.

## Accepted Stage 4.4B Candidate Administration

Backend and protected frontend administration support:
- candidate statuses `new`, `in_review`, `contacted`, `closed`, `archived`;
- authenticated list/detail/status endpoints;
- immutable consent evidence;
- authenticated private-photo access only through application ID;
- private media integrity/confinement checks;
- `private, no-store` sensitive responses;
- CSRF-protected status changes;
- protected `/admin` UI with session verification, status filtering/pagination and Blob-based private-photo display;
- no candidate deletion/editing/export/bulk operations.

## Accepted Stage 4.4C Content Administration

Authenticated content administration under `/api/v1/admin/content` and the protected frontend supports:
- News CRUD with publish/unpublish behavior and safe slug conflicts;
- RuTube Video CRUD with server-controlled provider/embed data;
- predefined Page list/detail/update only;
- immutable page keys with no page create/delete route;
- session authentication and CSRF for writes;
- generic validation/database failures;
- draft isolation from public APIs;
- no browser storage/autosave of unpublished editorial drafts.

## Accepted Admin Dashboard

The protected administration shell now has a real `/admin` overview instead of redirecting directly to Candidates:
- the navigation includes an exact-match `Обзор` entry for `/admin`;
- four quick-access cards link to Candidates, News, Video and Pages;
- the dashboard loads up to five most recent candidate applications through the already accepted authenticated candidate-list API;
- no new backend endpoint, database aggregate, total-count contract or invented statistic was introduced;
- candidate loading, empty, temporary-error/retry and expired-session handling reuse the accepted admin boundary;
- candidate rows expose only the same summary fields already allowed by the protected candidate-list API.

PR #52 was reviewed as a frontend-only three-file diff. Its first CI run was correctly blocked by Frontend typecheck on a JSX syntax error; after the targeted fix, Backend, Frontend and PostgreSQL Integration all passed. Controlled local E2E visual acceptance then confirmed `/admin` renders the `Обзор` navigation, four administration cards and real protected recent-candidate rows in the existing `astrea-e2e` runtime.

## Accepted Stage 4.4D Persistent Outbox and SMTP Worker

The email subsystem includes:
- durable outbox claim/retry/recovery state machine;
- PostgreSQL concurrency protection and guarded generation transitions;
- deterministic capped backoff and stale-processing recovery;
- machine-safe `last_error` codes with no raw SMTP/PII persistence;
- immutable candidate notification snapshots loaded in short DB sessions;
- UTF-8 plain-text + escaped HTML administrator notifications;
- verified STARTTLS/SMTP-SSL transport using the standard trust store;
- no candidate-photo attachment or private storage-key exposure;
- finite `process-email-outbox` execution only, not an in-process daemon;
- explicit at-least-once delivery semantics around the SMTP-accepted / DB-not-yet-marked-sent crash window.

Normal FastAPI startup does not require SMTP credentials. SMTP configuration is validated only by the finite worker/readiness paths.

## Accepted Guarded Candidate Form Integration

The public `/vstuplenie` page matches the backend multipart contract and remains fail-closed by default:
- frontend gate `VITE_CANDIDATE_FORM_ENABLED=false` by default;
- exact accepted backend field names;
- same-origin `FormData` submission;
- three required consent acknowledgements;
- JPG/PNG/WebP photo input with backend-authoritative validation;
- honeypot included;
- no candidate PII in browser storage, URLs, cookies, analytics or console output;
- generic status-mapped public errors;
- successful `201 {"accepted": true}` resets the form.

Public activation requires both frontend and backend gates to be explicitly enabled in an approved environment.

## Accepted Public News Integration

The public News routes are connected to the published-only content API. News list/detail rendering, loading/error/empty states and route behavior were reviewed and accepted. Unpublished news remains excluded by the backend public boundary.

## Accepted Public Video Integration

The public Video route is connected to the published-only video API. It renders server-provided validated RuTube embed URLs and source metadata without accepting arbitrary iframe HTML or provider-controlled markup.

## Accepted Public Managed Pages Integration

A deterministic Alembic data migration `20260824_0006` creates exactly five predefined managed-page rows on clean/existing deployments without overwriting matching existing rows. All are unpublished by default and the data-migration downgrade is intentionally non-destructive because administrator-edited rows cannot be safely distinguished from original seed data.

Canonical managed-page registry:

| Key | Public route | Initial title |
| --- | --- | --- |
| `about` | `/o-lozhe` | `О ложе` |
| `lodges_spb` | `/lozhi-sankt-peterburga` | `Ложи Санкт-Петербурга` |
| `principles` | `/celi-i-principy` | `Цели и принципы` |
| `faq` | `/faq` | `FAQ` |
| `contacts` | `/kontakty` | `Контакты` |

Accepted frontend behavior:
- each route fetches `/api/v1/pages/{key}` through the shared public-content client;
- published `page.title` is the single route H1;
- content is rendered as escaped plain React text with preserved whitespace, never as HTML/Markdown;
- no `dangerouslySetInnerHTML` or rich-text dependency;
- published/missing/error/loading states are distinct;
- backend `404` for missing/unpublished content becomes a neutral route-local unpublished state rather than a browser route 404;
- network/5xx errors expose an explicit retry action;
- in-flight requests are aborted on unmount/route change;
- the About heraldry section remains independent of managed-content publication state.

Controlled E2E acceptance confirmed the complete chain `migration -> DB -> Admin Pages -> publish -> public API -> public React route -> unpublish -> public 404/neutral route state`. The E2E database was returned to the seeded unpublished placeholder state after the test.

## Accepted Stage 5.1 Production-like Runtime Foundation

The repository includes a locally validated Docker/Compose/Nginx/PostgreSQL runtime with:
- finite Alembic `migrate` service;
- internal backend/database networking;
- frontend served by Nginx;
- persistent PostgreSQL and private-media volumes;
- non-root backend uid `10001`;
- fail-closed candidate gates;
- backend/private database ports not published to the host.

## Accepted Stage 5.2 Deployment Security Hardening

Accepted runtime hardening includes:
- dedicated `edge` and internal `data` networks;
- Uvicorn proxy trust restricted to the configured Nginx IP;
- Nginx overwriting forwarding headers so caller-supplied `X-Forwarded-For` cannot control limiter identity;
- generic request body limit of 1 MiB with a 12 MiB exception only for the exact candidate multipart endpoint;
- finite proxy timeouts;
- restrictive CSP, `Permissions-Policy`, `Referrer-Policy`, `nosniff` and `SAMEORIGIN` headers;
- read-only hardened backend/migrate container roots, dropped capabilities and `no-new-privileges`;
- no HSTS/TLS until the real HTTPS deployment.

If Stage 5.5 introduces a CDN/load balancer/additional reverse proxy, the trusted client-IP chain must be re-reviewed rather than automatically extended.

## Accepted Stage 5.3A Backup and Restore Foundation

Profile-only finite backup/restore operations capture PostgreSQL and private candidate media as one managed backup set. Backup uses custom-format `pg_dump`, compressed media, metadata and SHA-256 checksums; incomplete sets are not exposed as final backups. Restore validates checksums, dump readability and archive safety before destructive work and requires explicit destructive/quiescence confirmations.

Destructive validation was performed only in a disposable Compose project, not against the normal Astrea volumes.

## Accepted Stage 5.3B Operations, Retention and Scheduling

Accepted operations infrastructure includes:
- profile-only finite email-worker and prune services;
- automatic retention baseline of 14 validated automatic backup sets;
- separate explicit pruning with dry-run default;
- host `flock` orchestration;
- reviewed backup-directory provisioning for uid/gid `10001:10001` mode `0700`;
- systemd oneshot/timer templates for backup, email-worker and prune.

Repository code does not install/enable systemd units. Real Linux-host execution remains a Stage 5.5 production task.

## Accepted Stage 5.3C SMTP Readiness Implementation

The repository includes a finite non-sending `check-smtp` command that reuses the real delivery transport path for secure connection/authentication checks without sending mail. `email-worker` and `smtp-check` use the dedicated outbound `mail-egress` network; database/private operational services remain on the internal data boundary.

Code/infrastructure readiness is accepted. Live provider DNS/TLS/authentication, sender authorization and real delivery behavior remain unverified until external credentials/service-mailbox details are provisioned outside Git.

## Accepted CI Foundation

The repository now has a minimal GitHub Actions quality gate in `.github/workflows/ci.yml`:
- runs for pull requests targeting `main` and pushes to `main`;
- workflow token permissions are limited to `contents: read` plus GitHub metadata read;
- concurrency cancels superseded runs for the same workflow/ref;
- Backend job uses Python 3.13, installs `.[dev]`, runs Ruff and the full pytest suite;
- Frontend job uses Node 22, installs from the committed lockfile with `npm ci`, then runs typecheck, lint and production build;
- PostgreSQL Integration job uses a temporary PostgreSQL 16.4 service container matching the production Compose major/minor baseline, installs backend runtime dependencies, runs `alembic upgrade head` on an empty database, verifies the database revision equals the repository Alembic head, and verifies the exact five predefined managed pages remain unpublished with the accepted seed content;
- official `actions/checkout`, `actions/setup-python` and `actions/setup-node` are on Node-24-based v6 majors;
- no SMTP credentials, candidate/legal activation, production secrets or deployment operations are part of CI.

PR #48 provided the first controlled CI acceptance for the independent Backend and Frontend gates. After correcting the initial official-action majors to avoid the GitHub Node-20 deprecation warning, the final PR run completed successfully with both jobs green. PR #50 added and accepted the PostgreSQL Integration gate: PostgreSQL 16.4 became healthy, Alembic applied every migration from an empty database through `20260824_0006`, the resulting database revision matched the repository Alembic head, and the five predefined managed-page rows matched the accepted titles, placeholder content and `is_published=false`. The same PR also passed Backend with Ruff plus `293 passed, 1 skipped` and Frontend with `npm ci`, typecheck, lint and production build.

Repository governance is now accepted alongside CI: GitHub default branch is `main`, an active `Protect main` ruleset targets the default branch, and its required checks are `Backend`, `Frontend` and `PostgreSQL Integration`. GitHub reports `main` as protected. This protection is ruleset-based; classic branch protection remains unused. No extra review, signed-commit, deployment or similar rules were enabled as part of this baseline.

## Stage 5.4 Controlled End-to-End Acceptance

Status: **partially complete, not globally accepted**.

Completed candidate technical acceptance evidence in the controlled `astrea-e2e` environment:
- both candidate gates were temporarily enabled only for the controlled test and later restored to disabled;
- a synthetic candidate application was submitted successfully through the public form;
- PostgreSQL contained the candidate row, exactly three required consent rows with the controlled draft version identifiers, and one pending outbox row;
- private JPEG storage was readable through the storage layer, metadata size matched and file mode was `0600`;
- protected Admin Candidate detail displayed the synthetic candidate/private photo/consents;
- candidate status update persisted successfully;
- unauthenticated candidate-photo access returned `401`;
- cleanup restored both public/backend candidate gates to disabled.

Caveat: the controlled storage check confirmed normalized private JPEG persistence, but a separate EXIF-specific E2E proof was not captured and must not be overstated.

Remaining blockers for full Stage 5.4 acceptance:
- approved final privacy/personal-data/legal texts and production version identifiers;
- live SMTP-provider/service-mailbox connectivity, TLS/authentication and sender authorization using credentials outside Git;
- actual administrator-notification delivery portion of the controlled candidate flow.

Per current project direction, candidate legal activation and SMTP/mail work remain intentionally frozen until client infrastructure/mailbox information is available. Candidate intake stays disabled meanwhile.

## Stage 5.5 Production Deployment

Status: pending.

Requires client production infrastructure details, expected to include:
- VPS access;
- production domain/subdomain decision;
- DNS and TLS;
- external root-controlled environment/secrets provisioning;
- service mailbox / SMTP provider details;
- real backup directory provisioning;
- systemd unit/timer installation and validation;
- trusted-proxy revalidation against the real topology;
- final controlled acceptance and cutover.

No deployment is performed without explicit approval.

## Security

Main security risk: candidate forms contain personal data and photos.

Security requirements:
- HTTPS in production;
- private candidate data;
- non-public candidate photos;
- authenticated admin;
- secrets only through external environment provisioning;
- backup policy;
- server-side validation;
- upload validation and image normalization;
- anti-spam/rate limiting;
- persistent consent records;
- published-only public editorial APIs;
- no arbitrary HTML/embed ingestion;
- no production write/deploy actions without explicit approval.

The `religion` field remains disabled unless separately approved legal wording and processing basis for special-category personal data are provided.

## Current Next Steps

1. **Public managed content - accepted.** News, Video and five predefined managed public pages are connected to the public APIs and reviewed; managed-page controlled E2E is complete.
2. **Admin Dashboard - accepted.** `/admin` is now a real protected overview with four quick-access cards and up to five recent candidate applications through the existing authenticated API; local E2E visual acceptance is complete.
3. **CI Foundation + PostgreSQL Integration - accepted.** GitHub Actions runs three independent gates on PRs to `main` and pushes to `main`: Backend, Frontend and real PostgreSQL migration/seed verification.
4. **Repository governance - accepted.** GitHub default branch is `main`; the active `Protect main` ruleset requires Backend, Frontend and PostgreSQL Integration, and GitHub reports `main` as protected. The historical seed `master` branch remains untouched for now.
5. **Candidate technical acceptance - partially complete.** Core form/persistence/private-media/admin/security flow was exercised with synthetic data, but full Stage 5.4 remains blocked by legal and live SMTP requirements.
6. **Legal candidate activation - deferred/frozen.** Do not activate candidate intake or finalize legal version identifiers until approved client texts are available.
7. **SMTP live verification - deferred/frozen.** Do not request/use production credentials until the client service-mailbox/provider arrangement is known; repository readiness remains accepted.
8. **Stage 5.5 production infrastructure - pending.** Resolve VPS, domain/subdomain, DNS/TLS, secrets, service mailbox, backup/systemd provisioning and final cutover.

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.