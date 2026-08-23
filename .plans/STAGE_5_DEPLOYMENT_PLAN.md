# Stage 5 Deployment Plan

Status: accepted through Stage 5.3C implementation. Controlled acceptance and production deployment remain pending, including live SMTP-provider verification with external credentials before real notification delivery.

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

## Stage 5.3A - Backup and restore foundation

Status: accepted.

Goal: prove that PostgreSQL and private candidate media can be captured and restored together as one explicitly managed backup set before adding scheduling, pruning or production provisioning.

Implemented:
- profile-only one-shot `backup` and `restore` Compose services using PostgreSQL 16.4 operational tooling;
- operations services attach only to the internal `data` network, expose no host ports and never start with the ordinary runtime unless the `ops` profile is explicitly selected;
- backup output defaults to the ignored host `backups/` path through `ASTREA_BACKUP_ROOT`;
- backup private-media mount is read-only, while restore receives the required read-write private-media mount;
- both operations run as uid/gid `10001:10001`, matching the accepted backend private-media owner model;
- backup uses restrictive `umask 077`, PostgreSQL custom-format `pg_dump --no-owner --no-acl`, compressed private-media archive, non-secret metadata and SHA-256 checksums;
- safe generated/operator backup IDs are path-restricted; incomplete sets stay under `.incomplete.*` and the final directory appears only after dump, media archive, metadata and checksums all exist;
- backup refuses to run unless the operator explicitly acknowledges that application writes are quiesced;
- restore refuses to run without an explicit backup ID, destructive confirmation and backend-stopped acknowledgement;
- restore validates exactly one checksum each for the known `database.dump` and `private-media.tar.gz` paths, rejects unknown/duplicate manifest entries and never lets manifest filenames select arbitrary filesystem paths;
- metadata identity is validated without sourcing executable metadata;
- `pg_restore --list`, checksum validation, archive-path/type validation and isolated media staging complete before the first destructive restore action;
- archive restore rejects traversal, symlinks, hardlinks and non-regular/non-directory special entries;
- PostgreSQL restore uses `--clean --if-exists --no-owner --no-acl --single-transaction --exit-on-error`;
- media replacement occurs only from the already validated staging tree;
- no Docker socket, privileged mode, application source mount, automatic retention deletion, scheduler, SMTP, TLS, legal version or candidate activation is introduced.

Validated in disposable project `astrea-backup-review` only:
- normal and `ops` Compose configuration rendered successfully;
- backup/restore operations image build passed and shell syntax checks passed;
- synthetic private-media probe used production-like uid 10001 ownership, directory mode `0700` and file mode `0600`, and was successfully archived/read;
- valid backup set contained database dump, private-media archive, metadata and checksums with restrictive permissions and no leftover incomplete directory;
- backup without quiescence acknowledgement failed without creating a final backup set;
- restore without destructive confirmation or without backend-stopped acknowledgement failed before any data change;
- incomplete checksum manifest, deliberately corrupted artifact and an unsafe archive with a recomputed valid checksum were all rejected before `pg_restore`, leaving database and media unchanged;
- database state was changed `before-backup -> after-backup -> before-backup` by restore;
- private-media probe was changed `before-backup -> after-backup -> before-backup` by restore;
- restored backend became healthy as uid 10001 and could read the restored probe file;
- only disposable `astrea-backup-review_*` containers/volumes were destructively removed; normal `astrea` volumes were not used or deleted;
- both candidate activation gates remained `false`.

Known production provisioning requirement:
- the real VPS host backup directory must be provisioned writable by uid 10001 before production backup execution. Stage 5.3B now provides the reviewed provisioning script; actual execution remains deferred to Stage 5.5.

## Stage 5.3B - Operations, retention and scheduling

Status: accepted.

Goal: make the accepted runtime and backup foundation operable on a real host without embedding long-running operational loops into FastAPI.

Implemented:
- profile-only finite `email-worker` service that runs `python -m app.cli process-email-outbox`, has no private-media mount or host port, and retains the hardened non-root backend container model; Stage 5.3C adds its reviewed outbound `mail-egress` network while retaining internal `data` access for PostgreSQL;
- profile-only finite `prune` service with no network access, no PostgreSQL/private-media mounts, read-only container root and only the backup-root bind mount writable;
- technical retention baseline of 14 newest completed automatic backup sets, configurable within the validated 7..365 range;
- backup metadata now records `backup_origin=automatic|operator`; automatic pruning requires both the generated timestamp/suffix ID format and `backup_origin=automatic`;
- operator/custom backups, generated-looking operator IDs, legacy no-origin backups, incomplete sets, symlinks and malformed sets are excluded from automatic pruning;
- pruning is a separate explicit operation with safe dry-run default and destructive `PRUNE_AUTOMATIC_BACKUPS` confirmation; backup creation never performs implicit pruning;
- host-side `astrea-ops.sh` orchestrates `backup`, `email-worker`, `smtp-check` and `prune`, using one `flock` lock to prevent operational overlap; `smtp-check` was added in Stage 5.3C and remains manual/unscheduled;
- backup orchestration records whether backend was originally running, stops it cleanly to establish write quiescence, runs the accepted finite backup with explicit acknowledgement, and restores the original backend-running state on success or failure while preserving failure exit status;
- restore remains deliberately manual and is not exposed through the scheduler wrapper;
- `provision-backup-dir.sh` creates only an explicitly validated backup path, rejects dangerous roots/final symlinks, sets uid/gid `10001:10001` and mode `0700`, and never recursively changes parent trees;
- safe non-secret `astrea-ops.env.example` defines project/env/backup paths, retention count and Compose project name without credentials;
- systemd oneshot template delegates to the reviewed host script through `/bin/sh`, uses `/etc/astrea/ops.env`, `UMask=0077`, finite startup timeout and journald stdout/stderr;
- timer templates define daily backup around 03:30 with randomized delay, finite email-worker execution every five minutes, and weekly Sunday pruning around 04:30;
- no systemd unit is installed/enabled by repository code; no in-process daemon, Docker socket orchestration, SMTP credential, TLS, legal version or candidate activation is introduced.

Validated locally / with isolated harnesses:
- shell syntax checks passed for modified/new POSIX scripts;
- normal and `ops` Compose configurations rendered successfully;
- backup/restore/prune operations images and the finite email-worker path built successfully where applicable;
- email-worker without valid SMTP configuration failed closed with the accepted generic `Email outbox configuration is invalid` result and performed no real delivery;
- retention dry-run over 16 realistic automatic synthetic sets reported two deletions while deleting nothing;
- confirmed destructive retention reduced 16 eligible automatic sets to the newest 14 only;
- ordinary manual backup, generated-looking operator backup, legacy no-origin backup, malformed metadata and incomplete data remained untouched;
- invalid retention values failed closed without deletion;
- automatic backup metadata wrote `backup_origin=automatic`, explicit-ID backup metadata wrote `backup_origin=operator`, and legacy no-origin backup remained restorable;
- disposable provisioning test created a mode `0700`, uid/gid `10001:10001` directory and rejected an existing final symlink without changing its target;
- fake `docker`/`flock` host harness proved backup success returned `0`, forced backup failure preserved its non-zero status, and backend was restored to its original running state in both paths;
- normal `astrea` volumes were untouched and no normal-project `down -v` was used;
- both candidate activation gates remained `false`.

Production verification note:
- actual Linux host execution, systemd unit loading/enabling, `/etc/astrea/*.env` provisioning, `/var/backups/astrea` provisioning and timer runtime behavior remain intentionally deferred to Stage 5.5 on the real VPS.

## Stage 5.3C - SMTP readiness

Status: accepted for code/infrastructure readiness. Live provider verification remains a production/test-environment prerequisite because no real SMTP credentials were used or committed.

Goal: provide a safe, finite way to verify the external mail path required for administrator notifications without committing credentials, sending a test message, or coupling SMTP delivery to FastAPI startup.

Implemented:
- finite `python -m app.cli check-smtp` command that loads the accepted SMTP settings, validates configuration, establishes the same secure SMTP session used by real delivery, authenticates when credentials are configured, and exits without sending a message;
- `SmtpEmailTransport.check_connection()` shares the same internal secure-session path as `send()`, avoiding a second SMTP implementation and preserving the accepted STARTTLS/SMTP-SSL behavior;
- STARTTLS uses `ssl.create_default_context()`, `EHLO`, verified `STARTTLS`, a second `EHLO`, and optional authentication; SMTP-SSL uses `SMTP_SSL` with the verified default context and optional authentication;
- readiness never invokes `send_message`, `sendmail`, `MAIL FROM`, `RCPT TO` or `DATA`, and does not touch candidate records, outbox rows or private media;
- CLI failures are intentionally generic: invalid settings produce `SMTP readiness configuration is invalid.` and connection/authentication/provider failures produce `SMTP readiness check failed.` without exposing provider exception text or secrets;
- dedicated non-internal `mail-egress` Compose network provides outbound SMTP connectivity without publishing inbound ports;
- `email-worker` attaches to internal `data` plus `mail-egress`, while profile-only `smtp-check` attaches only to `mail-egress`, has no database dependency, no volumes, no host ports and no `edge` attachment;
- the existing `data` network remains `internal: true`; `db`, `migrate`, `backup`, `restore` and `prune` are not attached to `mail-egress`;
- host `astrea-ops.sh` supports a manual finite `smtp-check` operation under the existing global `flock`; no `smtp-check` timer or background loop is introduced;
- actual credentials continue to belong only in the external root-controlled environment file, not in Git, repository scripts or unit files;
- candidate activation gates remain disabled.

Validated without real provider credentials:
- targeted email/CLI tests: 28 passed;
- full backend suite: 290 passed, 1 skipped, 14 existing warnings;
- Ruff: all checks passed;
- normal and `ops` Compose configurations rendered successfully;
- normal runtime remains limited to `db`, `migrate`, `backend` and `web`;
- `email-worker` and `smtp-check` images built successfully;
- missing SMTP configuration failed closed with the generic configuration message;
- valid synthetic configuration pointed at an unreachable endpoint failed closed with the generic readiness failure message;
- tests prove STARTTLS and SMTP-SSL readiness use the verified context and optional login while never calling `send_message`;
- no real SMTP credential was used or tracked and no real email was sent;
- both candidate activation gates remained `false`.

External verification still required before real notification delivery:
- live provider DNS/network reachability;
- live CA/TLS handshake against the chosen provider;
- authentication with credentials supplied outside Git;
- sender authorization for the configured `SMTP_FROM_EMAIL`;
- recipient/delivery behavior through the real provider. The non-sending `check-smtp` command can verify connectivity/TLS/authentication safely; actual delivery is exercised only in the controlled acceptance flow.

## Stage 5.4 - Controlled end-to-end acceptance

Status: pending.

Goal: exercise the full application flow in a controlled environment before public production activation.

Prerequisites:
- approved privacy policy and personal-data consent text;
- approved server-controlled legal version identifiers;
- Stage 5.2 deployment/security hardening accepted;
- Stage 5.3 operational and SMTP implementation accepted;
- approved test/production SMTP configuration provisioned outside Git and live provider readiness verified before the email-delivery portion of acceptance.

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
- provision production PostgreSQL/private-media volumes, backup directory and real environment secrets;
- run migrations once and bootstrap the initial administrator explicitly;
- provision real SMTP settings outside Git, run the non-sending SMTP readiness check, then configure/install the reviewed external email-worker/backup/prune schedules;
- verify real Linux host operations, journald visibility, backup creation and a recoverable restore procedure before public candidate activation;
- smoke-test public routes, admin authentication, content administration and private-media boundaries;
- activate candidate intake only after legal, security and acceptance sign-off;
- retain a rollback path and backup of the existing site during cutover.

## Activation rule

Candidate intake remains disabled by default at both layers until all applicable legal, deployment/security, live SMTP-provider, operations and controlled-acceptance prerequisites are satisfied. The `religion` field remains disabled unless separately approved for special-category personal-data processing.

## Review rule

Keep Stage 5 slices small. Do not mix production secrets, destructive server operations, legal activation, backup changes and unrelated application features into one change. Production writes/destructive actions require explicit approval.
