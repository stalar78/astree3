# Astrea

Astrea is the new official website for D.L. Astrea No. 3 in Saint Petersburg, replacing and evolving the existing mason-astrea.ru website.

Current stage: Stage 4 backend implementation, guarded public candidate-form integration, Stage 5.1 production-like runtime foundation, Stage 5.2 deployment security hardening, Stage 5.3A backup/restore foundation, Stage 5.3B operations/retention/scheduling and Stage 5.3C SMTP readiness implementation are accepted. Candidate intake activation remains deferred pending approved legal texts, live SMTP-provider verification with external credentials, controlled acceptance and production deployment prerequisites.

The approved public design is documented in `docs/STAGE_2_DESIGN_FREEZE.md`. The production public frontend lives in `frontend/` and was accepted after visual and technical review. The backend foundation, public content domain, guarded candidate-intake pipeline, closed admin authentication, candidate administration API, content administration API, persistent email-outbox state machine, SMTP worker execution and non-sending SMTP readiness check live in `backend/`; protected candidate/content administration and the guarded public candidate form live in the production frontend. The accepted production-like runtime, security boundary, backup/restore foundation, host operations templates and dedicated mail-egress boundary live in `infra/` plus the backend/frontend Dockerfiles and Nginx configuration.

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
- Stage 5 deployment plan: `.plans/STAGE_5_DEPLOYMENT_PLAN.md`
- Requirements: `docs/REQUIREMENTS.md`
- Project blueprint: `PROJECT_BLUEPRINT.md`

## Current Implementation

- `frontend/` - accepted production public frontend, guarded candidate-application form integration, protected candidate administration and Stage 4.4C2 protected content administration UI; public candidate submission remains intentionally disabled by default through `VITE_CANDIDATE_FORM_ENABLED=false`
- `backend/` - accepted FastAPI/PostgreSQL foundation, Stage 4.2 public content API, Stage 4.3 guarded candidate-intake/private-photo pipeline, Stage 4.4A closed server-side admin authentication, Stage 4.4B1 authenticated candidate administration/private-photo API, Stage 4.4C1 authenticated content administration API, Stage 4.4D1 persistent outbox state machine, Stage 4.4D2 SMTP notification rendering/transport plus one-shot email-worker execution, and Stage 5.3C non-sending `check-smtp` readiness command
- `infra/` - accepted Stage 5.1/5.2 Docker Compose runtime and security boundary, Stage 5.3A profile-only backup/restore operations for PostgreSQL and private media, Stage 5.3B finite email-worker/prune services plus host/systemd operations templates, and Stage 5.3C dedicated `mail-egress` networking plus profile-only `smtp-check`

The Docker runtime has been exercised locally through Docker Desktop: images build successfully, PostgreSQL/backend/web become healthy, migrations complete successfully, `/api/v1/health` and public/admin SPA deep links return through Nginx, and only `127.0.0.1:8080` is published to the host. The backend runs as uid `10001` with a read-only root filesystem, dropped capabilities and no-new-privileges while retaining write access only to bounded tmpfs paths and the private-media volume.

The accepted Stage 5.2 proxy boundary makes Nginx authoritative for client forwarding and Uvicorn trusts proxy headers only from the configured Nginx edge IP. Incoming `X-Forwarded-For` is overwritten rather than appended, and the spoof-resistance smoke test confirmed that changing attacker-supplied forwarding headers cannot reset the application login rate limiter. The generic Nginx body limit is 1 MiB, with a 12 MiB exception only for the exact candidate multipart endpoint. CSP, `Permissions-Policy`, `Referrer-Policy`, `nosniff` and `SAMEORIGIN` headers are active; HSTS/TLS remain intentionally deferred to the real VPS/HTTPS deployment.

Stage 5.3A adds one-shot `backup` and `restore` services behind the explicit Compose `ops` profile. A backup set contains a PostgreSQL custom-format dump, compressed private-media archive, non-secret metadata and SHA-256 checksums; incomplete sets are not exposed as final backups. Backup requires explicit write-quiescence acknowledgement, while restore requires explicit destructive and backend-stopped confirmations. Restore validates both known artifacts, metadata, PostgreSQL dump readability and private-media archive safety before destructive work, then restores PostgreSQL in a single transaction and replaces media from a validated staging tree. Destructive validation was performed only in the disposable `astrea-backup-review` project: database and private-media probes were changed from `before-backup` to `after-backup` and successfully restored to `before-backup`, while corrupted/incomplete/unsafe backup cases were rejected before `pg_restore`. Normal `astrea` volumes were not used for destructive testing.

Stage 5.3B adds a finite profile-only `email-worker`, an isolated profile-only `prune` operation, host-level `flock` orchestration and systemd oneshot/timer templates. Automatic retention keeps the newest 14 validated automatic backup sets by default; operator/custom, generated-looking operator, legacy no-origin, incomplete and malformed backup sets are excluded from auto-pruning. Backup metadata explicitly records automatic/operator origin. The host backup wrapper stops a previously running backend to establish write quiescence, runs backup, and restores the original backend-running state while preserving failure status. Daily backup, five-minute email-worker and weekly prune timers are declared but are not installed or enabled by repository code. Production backup-directory provisioning is defined for uid/gid 10001 with mode `0700`. Real Linux host/systemd execution remains deferred to Stage 5.5.

Stage 5.3C adds a finite non-sending `check-smtp` command that reuses the same verified STARTTLS/SMTP-SSL connection and authentication path as real email delivery. A dedicated non-internal `mail-egress` network provides outbound SMTP reachability: `email-worker` uses `data + mail-egress`, while profile-only `smtp-check` uses `mail-egress` only and has no database dependency, volumes, host ports or `edge` attachment. The internal `data` network remains `internal: true`. Readiness failures are generic and do not expose provider exception text or credentials. Targeted tests reported 28 passed; the full backend suite reported 290 passed, 1 skipped and 14 existing warnings; Ruff and normal/ops Compose validation passed; both mail helper images built successfully. Missing configuration and an unreachable synthetic endpoint failed closed without sending mail. Live provider DNS/TLS/authentication and sender authorization remain intentionally unverified until credentials are provisioned outside Git.

Admin authentication uses Argon2id passwords, explicit initial-admin bootstrap, server-side opaque sessions, `HttpOnly` session cookies, separate CSRF tokens and process-local login rate limiting. There is no public/admin registration, JWT or browser `localStorage` authentication.

Candidate administration is available through authenticated `/api/v1/admin/candidates` routes and the protected `/admin` frontend. Candidate photo storage keys and private filesystem paths are not exposed, private photos are fetched only through the authenticated admin endpoint, and status mutations/logout use the accepted CSRF flow.

Content administration is available through authenticated `/api/v1/admin/content` routes and protected `/admin/news`, `/admin/videos` and `/admin/pages` frontend routes. News and RuTube videos support protected create/read/update/delete operations, while predefined pages support only authenticated list/detail/update; page identities cannot be created, deleted or renamed. Draft content remains excluded from the public Stage 4.2 endpoints, write `403` errors remain on-page, and unpublished editorial state is not persisted in browser storage or URLs.

The public `/vstuplenie` candidate form matches the accepted multipart backend contract, including photo upload, honeypot, three required consent fields and the exact Saint Petersburg acknowledgement. It uses uncontrolled form controls and same-origin `FormData`, does not persist candidate PII in browser storage/URLs/cookies, and exposes only generic status-mapped public errors. The separate frontend gate is fail-closed and defaults to disabled.

Email delivery uses the persistent `email_outbox` state machine plus a finite `process-email-outbox` worker command. The worker validates SMTP configuration only at execution time, recovers stale work, claims a bounded committed batch, builds an immutable candidate snapshot in a short database session, renders UTF-8 plain/HTML administrator notifications, performs verified STARTTLS/SMTP-SSL delivery with no database transaction open, and records success/failure through guarded transitions. Candidate photos are not attached to email; the notification links only to the authenticated admin candidate page. The delivery model remains intentionally at-least-once around the SMTP-accepted/DB-not-yet-marked-sent crash window. Stage 5.3C provides the non-sending readiness check and outbound network path, but real provider credentials/connectivity remain external deployment inputs.

Candidate intake is disabled by default at both layers: `VITE_CANDIDATE_FORM_ENABLED=false` keeps the public form non-operational, while `CANDIDATE_INTAKE_ENABLED=false` keeps the backend route unregistered. Both must remain disabled until approved privacy/consent documents and server-controlled legal version identifiers are available, live SMTP-provider readiness is verified outside Git, and controlled end-to-end acceptance succeeds. The production trusted-proxy chain must be re-verified if Stage 5.5 introduces a CDN, load balancer or additional reverse proxy.

## Important

`_ref/` contains local client source materials and is never committed or used as a runtime application directory.
