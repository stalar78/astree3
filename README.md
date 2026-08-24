# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 4 backend implementation, guarded public candidate-form integration, Stage 5.1 production-like runtime foundation, Stage 5.2 deployment security hardening, Stage 5.3A backup/restore foundation, Stage 5.3B operations/retention/scheduling, Stage 5.3C SMTP readiness implementation and CI Foundation are accepted. Public News, Video and five predefined managed-page integrations are accepted. Controlled candidate-workflow acceptance is partially complete; candidate intake activation remains deferred pending approved legal texts/version identifiers, live SMTP-provider verification and production deployment prerequisites.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. The production public frontend lives in `frontend/` and was accepted after visual and technical review. The backend foundation, public content domain, guarded candidate-intake pipeline, closed admin authentication, candidate administration API, content administration API, persistent email-outbox state machine, SMTP worker execution and non-sending SMTP readiness check live in `backend/`; protected candidate/content administration, public News/Video/managed-page integration and the guarded public candidate form live in the production frontend. The accepted production-like runtime, security boundary, backup/restore foundation, host operations templates and dedicated mail-egress boundary live in `infra/` plus the backend/frontend Dockerfiles and Nginx configuration. Repository quality gates run through `.github/workflows/ci.yml`.

## Application Scope

- Public informational website
- News section
- External video section, primarily RuTube URLs
- Candidate application form with photo upload
- Candidate application persistence
- Formatted email notifications
- Protected administration panel
- Editable predefined content
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
- Stage 5 deployment plan: `.plans/STAGE_5_DEPLOYMENT_PLAN.md`
- Requirements: `docs/REQUIREMENTS.md`
- Project blueprint: `PROJECT_BLUEPRINT.md`

## Current Implementation

- `frontend/` - accepted production public frontend, guarded candidate-application form integration, protected candidate/content administration, published News/Video integration and five predefined public managed-page routes; public candidate submission remains intentionally disabled by default through `VITE_CANDIDATE_FORM_ENABLED=false`
- `backend/` - accepted FastAPI/PostgreSQL foundation, public content API, guarded candidate-intake/private-photo pipeline, closed server-side admin authentication, authenticated candidate administration/private-photo API, authenticated content administration API, persistent outbox state machine, SMTP notification rendering/transport plus one-shot email-worker execution, non-sending `check-smtp` readiness command, and Alembic `20260824_0006` deterministic predefined-page bootstrap
- `infra/` - accepted Stage 5.1/5.2 Docker Compose runtime and security boundary, Stage 5.3A profile-only backup/restore operations for PostgreSQL and private media, Stage 5.3B finite email-worker/prune services plus host/systemd operations templates, and Stage 5.3C dedicated `mail-egress` networking plus profile-only `smtp-check`
- `.github/workflows/ci.yml` - accepted read-only CI Foundation for pull requests to `main` and pushes to `main`: Backend uses Python 3.13 with Ruff and pytest; Frontend uses Node 22 with `npm ci`, typecheck, lint and production build

The Docker runtime has been exercised locally through Docker Desktop: images build successfully, PostgreSQL/backend/web become healthy, migrations complete successfully, `/api/v1/health` and public/admin SPA deep links return through Nginx, and only the configured localhost Nginx port is published to the host. The backend runs as uid `10001` with a read-only root filesystem, dropped capabilities and no-new-privileges while retaining write access only to bounded tmpfs paths and the private-media volume.

The accepted Stage 5.2 proxy boundary makes Nginx authoritative for client forwarding and Uvicorn trusts proxy headers only from the configured Nginx edge IP. Incoming `X-Forwarded-For` is overwritten rather than appended, and the spoof-resistance smoke test confirmed that changing attacker-supplied forwarding headers cannot reset the application login rate limiter. The generic Nginx body limit is 1 MiB, with a 12 MiB exception only for the exact candidate multipart endpoint. CSP, `Permissions-Policy`, `Referrer-Policy`, `nosniff` and `SAMEORIGIN` headers are active; HSTS/TLS remain intentionally deferred to the real VPS/HTTPS deployment.

Stage 5.3A adds one-shot `backup` and `restore` services behind the explicit Compose `ops` profile. A backup set contains a PostgreSQL custom-format dump, compressed private-media archive, non-secret metadata and SHA-256 checksums; incomplete sets are not exposed as final backups. Backup requires explicit write-quiescence acknowledgement, while restore requires explicit destructive and backend-stopped confirmations. Restore validates both known artifacts, metadata, PostgreSQL dump readability and private-media archive safety before destructive work, then restores PostgreSQL in a single transaction and replaces media from a validated staging tree. Destructive validation was performed only in the disposable `astrea-backup-review` project; normal Astrea volumes were not used for destructive testing.

Stage 5.3B adds a finite profile-only `email-worker`, an isolated profile-only `prune` operation, host-level `flock` orchestration and systemd oneshot/timer templates. Automatic retention keeps the newest 14 validated automatic backup sets by default; operator/custom, legacy/incomplete/malformed sets are excluded from auto-pruning. Daily backup, finite email-worker and weekly prune timers are declared but are not installed or enabled by repository code. Production backup-directory provisioning is defined for uid/gid 10001 with mode `0700`. Real Linux host/systemd execution remains deferred to Stage 5.5.

Stage 5.3C adds a finite non-sending `check-smtp` command that reuses the same verified STARTTLS/SMTP-SSL connection and authentication path as real email delivery. A dedicated non-internal `mail-egress` network provides outbound SMTP reachability: `email-worker` uses `data + mail-egress`, while profile-only `smtp-check` uses `mail-egress` only and has no database dependency, volumes, host ports or `edge` attachment. The internal `data` network remains `internal: true`. Readiness failures are generic and do not expose provider exception text or credentials. Live provider DNS/TLS/authentication and sender authorization remain intentionally unverified until credentials/service-mailbox details are provisioned outside Git.

Admin authentication uses Argon2id passwords, explicit initial-admin bootstrap, server-side opaque sessions, `HttpOnly` session cookies, separate CSRF tokens and process-local login rate limiting. There is no public/admin registration, JWT or browser `localStorage` authentication.

Candidate administration is available through authenticated `/api/v1/admin/candidates` routes and the protected `/admin` frontend. Candidate photo storage keys and private filesystem paths are not exposed, private photos are fetched only through the authenticated admin endpoint, and status mutations/logout use the accepted CSRF flow.

Content administration is available through authenticated `/api/v1/admin/content` routes and protected `/admin/news`, `/admin/videos` and `/admin/pages` frontend routes. News and RuTube videos support protected create/read/update/delete operations, while predefined pages support only authenticated list/detail/update; page identities cannot be created, deleted or renamed. Draft content remains excluded from the public endpoints, write `403` errors remain on-page, and unpublished editorial state is not persisted in browser storage or URLs.

Public News and Video routes consume the published-only content APIs. Video embeds use server-derived validated RuTube URLs and no arbitrary iframe HTML. Alembic migration `20260824_0006` ensures five predefined managed pages exist without overwriting matching rows: `about`, `lodges_spb`, `principles`, `faq`, `contacts`. They are unpublished by default. Their public routes render API title/content as escaped plain text, distinguish loading/unpublished/error states, provide retry for temporary failures and never use `dangerouslySetInnerHTML`. Controlled E2E verified Admin Pages -> publish -> public API -> public route -> unpublish/404/neutral route behavior, then restored the test page to its seeded unpublished placeholder state.

The public `/vstuplenie` candidate form matches the accepted multipart backend contract, including photo upload, honeypot, three required consent fields and the exact Saint Petersburg acknowledgement. It uses uncontrolled form controls and same-origin `FormData`, does not persist candidate PII in browser storage/URLs/cookies, and exposes only generic status-mapped public errors. The separate frontend gate is fail-closed and defaults to disabled.

Email delivery uses the persistent `email_outbox` state machine plus a finite `process-email-outbox` worker command. The worker validates SMTP configuration only at execution time, recovers stale work, claims a bounded committed batch, builds an immutable candidate snapshot in a short database session, renders UTF-8 plain/HTML administrator notifications, performs verified STARTTLS/SMTP-SSL delivery with no database transaction open, and records success/failure through guarded transitions. Candidate photos are not attached to email; the notification links only to the authenticated admin candidate page. The delivery model remains intentionally at-least-once around the SMTP-accepted/DB-not-yet-marked-sent crash window.

Controlled candidate technical acceptance has exercised synthetic form submission, persistence, exactly three controlled consent rows, pending outbox creation, private-photo storage/readback, protected admin review/status change and unauthenticated photo rejection. Both candidate gates were returned to disabled after the test. This does **not** make Stage 5.4 globally accepted: approved final legal texts/version IDs and live SMTP-provider delivery verification remain outstanding. A separate EXIF-specific E2E proof was not captured and must not be inferred from the general private-JPEG storage check.

Candidate intake is disabled by default at both layers: `VITE_CANDIDATE_FORM_ENABLED=false` keeps the public form non-operational, while `CANDIDATE_INTAKE_ENABLED=false` keeps the backend route unregistered. Both must remain disabled until approved privacy/consent documents and server-controlled legal version identifiers are available, live SMTP-provider readiness/delivery is verified outside Git, and the remaining controlled acceptance/production prerequisites succeed. The production trusted-proxy chain must be re-verified if Stage 5.5 introduces a CDN, load balancer or additional reverse proxy.

The GitHub repository default branch is `main`. CI PR #48 was accepted after the final Node-24-based official-action configuration produced successful independent Backend and Frontend jobs; the Backend run included Ruff plus `293 passed, 1 skipped`, and the Frontend run passed `npm ci`, typecheck, lint and production build. Branch-protection policy is not yet configured and remains a separate repository-governance decision.

Current project direction explicitly freezes candidate legal activation and SMTP/mail work until client infrastructure/service-mailbox information is available. Production VPS/domain or subdomain, DNS/TLS, external secrets, backup/systemd provisioning and final cutover remain pending Stage 5.5 tasks.

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
