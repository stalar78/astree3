# Stage 5 Deployment Plan

Status: accepted through Stage 5.2. Remaining operations, controlled acceptance and production deployment work is intentionally split into reviewed slices before candidate activation.

## Stage 5.1 - Production-like runtime foundation

Status: accepted.

Implemented:
- explicit-version backend Docker image with Python 3.13, Uvicorn/Alembic availability and non-root runtime user `astrea` (uid 10001);
- explicit-version multi-stage frontend image with Node build stage and Nginx runtime stage;
- Docker Compose topology: PostgreSQL `db`, finite `migrate`, FastAPI `backend`, Nginx `web`;
- PostgreSQL named persistent volume;
- private candidate-media named persistent volume mounted only into the backend;
- one-shot `alembic upgrade head` service that waits for healthy PostgreSQL and must complete successfully before backend readiness;
- Nginx React Router fallback and `/api/` reverse proxy to internal `backend:8000`;
- local host exposure limited to `127.0.0.1:8080`; PostgreSQL 5432 and backend 8000 remain unpublished;
- Nginx request-body baseline of 12 MiB for compatibility with the accepted 10 MiB candidate-photo limit plus multipart overhead;
- fail-closed defaults for `VITE_CANDIDATE_FORM_ENABLED=false` and `CANDIDATE_INTAKE_ENABLED=false`;
- safe `infra/.env.example` with no production credentials, SMTP secrets, admin password or legal-version identifiers;
- no source-code bind mounts, Redis, Celery, worker loop, TLS or production-domain configuration.

Validated locally:
- `docker compose ... config` passed;
- Docker image build passed;
- PostgreSQL, backend and web became healthy;
- migration service exited `0`;
- `/api/v1/health`, `/`, `/vstuplenie` and `/admin/login` returned successfully through Nginx;
- backend process ran as uid 10001 and could create/read/delete a temporary non-PII file in the mounted private-media volume;
- only `127.0.0.1:8080` was published to the host;
- clean shutdown completed without deleting named volumes;
- backend quality gate reported 280 passed, 1 skipped, 14 existing warnings; Ruff passed;
- frontend typecheck, lint and build passed.

## Stage 5.2 - Deployment security hardening

Status: accepted.

Implemented:
- dedicated Compose `edge` and internal `data` networks;
- `web` attached only to `edge`, `db` and `migrate` only to `data`, and `backend` as the sole service attached to both networks;
- configurable edge subnet and fixed Nginx proxy IP through `ASTREA_EDGE_SUBNET` / `ASTREA_PROXY_IP` safe defaults;
- Uvicorn proxy-header trust restricted to the configured Nginx proxy IP rather than wildcard trust;
- Nginx overwrites `X-Forwarded-For` and related forwarding headers from `$remote_addr` and clears the incoming standardized `Forwarded` header, preventing caller-supplied forwarding chains from controlling application limiter identity;
- accepted application-level candidate/admin-login rate limiters remain based on `request.client.host`, with existing configurable request/window settings exposed through Compose without changing application defaults;
- generic Nginx request-body limit reduced to 1 MiB while the exact `/api/v1/candidate-applications` endpoint receives a 12 MiB multipart allowance;
- finite reverse-proxy connect/send/read timeouts;
- `server_tokens off`;
- Nginx security headers: restrictive CSP, `Permissions-Policy`, `Referrer-Policy`, `X-Content-Type-Options: nosniff` and `X-Frame-Options: SAMEORIGIN`;
- CSP supports same-origin application/API resources, HTTPS editorial images, in-memory `blob:` private-photo display and approved RuTube frames without `unsafe-eval` or wildcard script/frame sources;
- backend and migrate containers hardened with read-only root filesystem, `cap_drop: ALL`, `no-new-privileges` and bounded writable tmpfs paths;
- non-root backend uid 10001 and backend-only writable private-media volume preserved;
- backend 8000 and PostgreSQL 5432 remain unpublished; only localhost Nginx HTTP is host-published;
- no HSTS, TLS certificates, production SMTP, legal versions or candidate activation introduced.

Validated locally:
- Compose config and image build passed;
- PostgreSQL/backend/web became healthy and migrate exited `0`;
- `nginx -t` passed;
- forwarded-header spoof smoke test using invalid admin login returned `401` then `429` despite changing attacker-supplied `X-Forwarded-For` between requests;
- generic oversized API traffic was rejected with `413` at the 1 MiB boundary;
- a synthetic 2 MiB request reached the disabled candidate endpoint and returned `404`, proving the exact path received the larger allowance;
- a synthetic 13 MiB candidate-path request was rejected with `413`;
- `/api/v1/health`, `/`, `/vstuplenie` and `/admin/login` returned successfully through Nginx;
- expected CSP/security headers were present on public and API responses;
- backend remained uid 10001, private media remained writable only to backend, and no private-media Nginx exposure existed;
- backend quality gate remained 280 passed, 1 skipped, 14 existing warnings; Ruff passed;
- frontend typecheck, lint and build passed;
- both candidate activation gates remained `false`.

Production note:
- the accepted trusted-proxy model assumes the container Nginx is the direct client-facing reverse proxy. If a CDN, load balancer or additional reverse proxy is introduced in Stage 5.5, client-IP trust must be re-evaluated against that actual topology rather than blindly extending the trusted chain.

## Stage 5.3 - Backup and operations

Status: pending.

Goal: make the accepted runtime operable and recoverable.

Planned scope:
- PostgreSQL backup procedure and retention baseline;
- private candidate-media backup procedure and retention baseline;
- documented restore verification for database + private media as one recoverable dataset;
- production environment/secrets provisioning approach without committing real `.env` files;
- explicit external scheduling for the finite `process-email-outbox` command, such as systemd timer or cron;
- worker execution/logging/failure visibility without converting it into an in-process daemon;
- production SMTP credential/connectivity verification;
- basic operational health/log inspection and restart procedures.

## Stage 5.4 - Controlled end-to-end acceptance

Status: pending.

Goal: exercise the full application flow in a controlled environment before public production activation.

Prerequisites:
- approved privacy policy and personal-data consent text;
- approved server-controlled legal version identifiers;
- Stage 5.2 deployment/security hardening accepted;
- Stage 5.3 required operational/SMTP pieces available.

Planned acceptance flow:
- explicitly enable both frontend and backend candidate gates only in the controlled test environment;
- submit test-only, non-real candidate data and an allowed image through Nginx;
- verify server validation, persistence, three consent records, private photo normalization/storage and pending email outbox creation;
- verify authenticated admin list/detail/private-photo access and status update;
- execute the one-shot email worker against the approved test SMTP path and verify the administrator notification;
- verify failure/error paths without exposing raw PII or private storage details;
- disable test activation again until final production approval if production prerequisites are not yet complete.

## Stage 5.5 - VPS production deployment and acceptance

Status: pending; requires client infrastructure.

Planned scope:
- provision Linux VPS and production DNS/domain routing;
- install/runtime prerequisites and production Docker Compose deployment;
- configure Nginx TLS/SSL using the approved domain and certificate process;
- re-verify the trusted client-IP/proxy chain against the actual Internet-facing topology;
- provision production PostgreSQL/private-media volumes and real environment secrets;
- run migrations once and bootstrap the initial administrator explicitly;
- configure SMTP and external email-worker schedule;
- verify backups before public candidate activation;
- smoke-test public routes, admin authentication, content administration and private-media boundaries;
- activate candidate intake only after legal, security and acceptance sign-off;
- retain a rollback path and backup of the existing site during cutover.

## Activation rule

Candidate intake remains disabled by default at both layers until all applicable legal, deployment/security, SMTP/operations and acceptance prerequisites are satisfied. The `religion` field remains disabled unless separately approved for special-category personal-data processing.

## Review rule

Keep Stage 5 slices small. Do not mix production secrets, destructive server operations, legal activation, backup changes and unrelated application features into one change. Production writes/destructive actions require explicit approval.
