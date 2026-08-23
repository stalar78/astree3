# Stage 4 Backend Plan

Status: accepted through Stage 4.4D2. The backend implementation slices defined in this plan are complete; guarded frontend candidate-form integration is also accepted. Candidate intake activation remains deferred pending legal and deployment/security prerequisites.

Stage 4 is intentionally split into small reviewed slices. The candidate workflow is high-risk because it handles personal data and photographs; it must not be implemented as one oversized change.

## Stage 4.1 - Backend foundation

Status: accepted.

Goal: establish a production-oriented FastAPI/PostgreSQL base without domain-feature sprawl.

Implemented:
- `backend/` application package;
- FastAPI app factory / application entrypoint;
- `/api/v1/health` endpoint;
- environment-based settings with no committed secrets;
- SQLAlchemy 2.x PostgreSQL integration via psycopg 3;
- plain `postgresql://` DSN normalization to the psycopg 3 dialect;
- session/dependency management;
- Alembic configuration and empty baseline migration capability;
- backend test setup with pytest;
- Ruff quality gate.

Not implemented in this slice:
- candidate submission;
- uploads;
- email sending/outbox processing;
- admin authentication;
- content CRUD;
- Redis/Celery;
- production credentials.

Acceptance completed:
- application foundation imports/creates successfully under test configuration;
- health endpoint passes;
- database configuration is environment-driven and validated;
- Alembic loads project metadata without domain tables or hard-coded credentials;
- pytest and Ruff checks pass;
- no secrets or generated local data committed.

## Stage 4.2 - Public content domain

Status: accepted.

Implemented:
- structured `pages`, `news_posts` and `videos` persistence;
- one Alembic migration creating only those three tables;
- published-only public read endpoints under `/api/v1`;
- stable validated news slugs and page keys;
- bounded `limit`/`offset` listing for news and videos;
- deterministic published-content ordering;
- RuTube-only external video validation with HTTPS, canonical 32-hex video IDs and derived embed URLs;
- no arbitrary iframe/embed HTML storage;
- provider consistency enforced in both the SQLAlchemy model and database constraint;
- public response schemas separated from persistence models.

Acceptance completed:
- draft/unpublished content is not returned publicly;
- no public content write routes exist;
- `Base.metadata` contains only `pages`, `news_posts`, `videos` for this domain slice;
- the video provider constraint is placed on `videos`, with regression coverage;
- no candidate/admin/email models or frontend changes were introduced;
- final reported checks: 54 pytest tests passed and Ruff passed.

## Stage 4.3 - Candidate intake and private media

Status: accepted.

Implemented in reviewed sub-slices:
- `candidate_applications`, `application_consents` and `email_outbox` persistence contracts;
- exact Saint Petersburg acknowledgement contract;
- private candidate-photo decoding, validation, metadata stripping and JPEG normalization;
- generated `candidate-photos/<uuid>.jpg` storage keys and private filesystem storage outside public roots;
- path-traversal protection, exclusive writes and cleanup support;
- transactional intake service creating one candidate application, exactly three consent rows and one pending outbox row;
- rollback/photo-cleanup guarantees for every pre-commit failure after photo storage;
- disabled-by-default multipart candidate POST endpoint;
- server-controlled legal document version identifiers;
- strict explicit consent parsing;
- honeypot protection;
- process-local MVP rate limiting without IP persistence;
- bounded upload reading before image decode;
- generic candidate validation/error responses that do not echo submitted PII.

Accepted flow:

```text
feature-gated multipart request
 -> authoritative server validation
 -> honeypot / rate-limit checks
 -> bounded upload read
 -> image decode/validation/normalization
 -> private generated file identity
 -> single DB transaction:
      candidate application
      exactly three consent records
      one pending email outbox row
 -> generic success response
```

Acceptance rules:
- PostgreSQL is the source of truth;
- candidate + consent + outbox persistence occurs before any email delivery attempt;
- failed email delivery cannot lose an accepted application;
- private photographs remain outside the public web root;
- original upload filenames and original image bytes are never persisted;
- image content is validated by actual Pillow decoding, not extension/MIME alone;
- normalized candidate photos are re-encoded as JPEG with unnecessary metadata removed;
- legal document versions come only from server settings, never from the client;
- `CANDIDATE_INTAKE_ENABLED` defaults to `false` and the candidate route is not registered when disabled;
- enabling intake requires all three configured legal version identifiers;
- no public candidate GET/photo route exists;
- `religion` remains disabled pending separate legal approval.

Final reported quality gate:
- 123 pytest tests passed;
- Ruff passed.

Activation remains deliberately deferred until approved privacy/consent documents and deployment/security review are complete.

## Stage 4.4 - Admin and operations

Status: accepted through Stage 4.4D2.

### Stage 4.4A - Admin authentication

Status: accepted.

Implemented in reviewed sub-slices:
- `admin_users` and `admin_sessions` persistence with Alembic migration `20260822_0003`;
- Argon2id password hashing and verification;
- explicit one-time initial-admin bootstrap with no startup side effects;
- opaque high-entropy session and CSRF tokens with only SHA-256 digests persisted;
- server-side session lookup with inactive/expired-session rejection;
- `POST /api/v1/admin/auth/login`;
- `POST /api/v1/admin/auth/logout`;
- `GET /api/v1/admin/auth/me`;
- `HttpOnly` session cookie, `SameSite=Strict`, `Secure` outside local/dev/test;
- separate browser-readable CSRF cookie and `X-CSRF-Token` verification;
- CSRF-protected logout and reusable authenticated-admin/CSRF dependencies for later admin writes;
- fixed session TTL with no sliding extension;
- app-scoped process-local login rate limiting without IP persistence or direct trust of `X-Forwarded-For`;
- dummy Argon2 verification for missing/inactive users to reduce username-enumeration timing differences;
- password rehash support in the same transaction as session creation;
- generic auth validation/credential/session/database errors without credential/token echo;
- no JWT, no `localStorage` authentication, no public/admin registration and no complex RBAC.

Final reported quality gate from `backend/`:
- 165 pytest tests passed;
- Ruff passed.

### Stage 4.4B - Candidate administration

Status: accepted.

#### Stage 4.4B1 - Candidate administration backend

Status: accepted.

Implemented:
- neutral operational candidate statuses: `new`, `in_review`, `contacted`, `closed`, `archived`;
- Alembic migration `20260822_0004` adding constrained/indexed candidate status with existing rows defaulted to `new`;
- authenticated `GET /api/v1/admin/candidates` with bounded pagination, status filtering and summary-only PII exposure;
- authenticated candidate detail with stored consent evidence and no outbox/internal storage disclosure;
- authenticated private candidate-photo endpoint addressed only by candidate application ID;
- private storage read through the existing storage abstraction with strict generated-key validation, traversal confinement, regular-file checks and final-symlink rejection where supported;
- JPEG media/recorded-size integrity checks before serving a private photo;
- `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff` on sensitive media responses;
- CSRF-protected candidate status updates with one commit and generic rollback/error behavior;
- no candidate deletion, editing, export, notes, bulk operations, public candidate reads or public photo aliases.

Final reported quality gate from `backend/`:
- 194 pytest tests passed, 1 platform-dependent symlink test skipped;
- Ruff passed.

#### Stage 4.4B2 - Candidate administration UI

Status: accepted.

Implemented:
- protected `/admin` route tree separate from the public `PageShell`;
- `/admin/login`, `/admin/candidates` and `/admin/candidates/:candidateId`;
- real server-session verification through `/api/v1/admin/auth/me` before protected candidate data is rendered;
- same-origin fetch-based API layer with no JWT, no browser auth-token storage and no JavaScript access to the `HttpOnly` session cookie;
- candidate status filtering and offset pagination with page size 20 and no invented total count;
- operational list state limited to non-sensitive `status`/`offset` URL parameters;
- candidate detail with read-only PII and human-readable immutable consent evidence;
- private photos fetched only by candidate application ID from the authenticated backend endpoint and rendered as revocable in-memory Blob URLs;
- status updates and logout using the accepted CSRF cookie/header flow;
- `401`, CSRF `403` and temporary `503`/network failures handled distinctly without false mutation/logout success;
- retry controls for temporary session/list failures;
- generic error presentation without raw server/proxy payload exposure;
- development-only Vite `/api` proxy while production remains same-origin;
- no candidate deletion/editing/export/bulk actions and no public link advertising admin access.

Final reported quality gate from `frontend/`:
- `npm run typecheck` passed;
- `npm run lint` passed;
- `npm run build` passed.

### Stage 4.4C - Content administration

Status: accepted.

#### Stage 4.4C1 - Content administration backend

Status: accepted.

Implemented:
- authenticated admin content routes under `/api/v1/admin/content`;
- news list/detail/create/update/delete over the existing `news_posts` table;
- news pagination with bounded `limit`/`offset`, optional `published` filter and deterministic `updated_at DESC, id DESC` ordering;
- server-managed news publication timestamps: first publication sets UTC time, unpublish/republish preserves the original timestamp;
- safe duplicate news-slug handling with `409` and rollback;
- optional news image references restricted to HTTPS absolute URLs or root-relative same-origin paths, with no server-side fetching or storage;
- video list/detail/create/update/delete over the existing `videos` table;
- accepted Stage 4.2 RuTube validator reused without weakening: canonical HTTPS RuTube source URLs, server-derived provider/embed URL, no iframe HTML or arbitrary providers;
- server-managed video publication timestamps with the same first-publish/unpublish/republish semantics as news;
- constrained page administration over existing `pages` rows only: list all pages ordered by key, detail by immutable key, and update only title/content/publication state;
- no page creation, page deletion, key mutation, arbitrary page-builder blocks or layout mutation;
- authenticated reads and accepted Stage 4.4A CSRF dependency for every admin content write;
- strict request schemas with `extra="forbid"`, strict JSON booleans, safe text/URL validation and generic scoped validation responses that do not echo submitted draft content;
- `Cache-Control: private, no-store` and `Pragma: no-cache` on admin content success/error responses;
- generic DB failure handling with rollback and no SQL/constraint/DSN leakage;
- mutation response boundary `flush -> refresh -> commit -> serialize`, with tests proving no database access occurs after a successful commit and refresh failures remain rollback-safe before persistence;
- existing Stage 4.2 public endpoints remain published-only and use the same PostgreSQL rows;
- no migration `0005`, no new content/revision/audit tables and the accepted eight-table metadata surface is unchanged.

Final reported quality gate from `backend/`:
- 231 pytest tests passed, 1 skipped;
- Ruff passed.

#### Stage 4.4C2 - Content administration UI

Status: accepted.

Implemented:
- protected admin navigation for Candidates, News, Video and Pages within the existing Stage 4.4B2 admin shell;
- protected routes for news/video lists, create/edit forms and existing-page editing outside the public `PageShell`;
- news list with bounded `limit=20`/offset pagination, `published` filtering and canonical browser URL state limited to `published`/`offset`;
- news create/edit/delete with server-owned publication timestamps, safe duplicate-slug `409` handling and explicit two-step deletion confirmation;
- news image references entered only as HTTPS/root-relative text values with no automatic preview, network fetch, upload or media library;
- RuTube video list/create/edit/delete with no provider selector, iframe editor, embed HTML or automatic external preview;
- predefined page list/edit limited to existing immutable keys and title/content/publication state, with no create/delete controls or page-builder surface;
- accepted same-origin session-cookie authentication and exact CSRF cookie/header flow reused for every write;
- `401`, CSRF `403` and temporary `503`/network failures handled distinctly without false mutation/logout success;
- retry controls for temporary session/list failures;
- generic error presentation without raw server/proxy payload exposure;
- development-only Vite `/api` proxy while production remains same-origin;
- no candidate deletion/editing/export/bulk actions and no public link advertising admin access.

Final reported quality gate from `frontend/`:
- `npm run typecheck` passed;
- `npm run lint` passed;
- `npm run build` passed.

### Stage 4.4D - Email outbox operations

Status: accepted through Stage 4.4D2.

#### Stage 4.4D1 - Persistent outbox state machine

Status: accepted.

Implemented:
- Alembic migration `20260823_0005` extending the existing `email_outbox` table only with timezone-aware `processing_started_at` and `next_attempt_at` fields;
- migration backfill for already-processing rows before applying the processing timestamp invariant;
- matching ORM/migration composite claim index `ix_email_outbox_status_next_attempt_id(status, next_attempt_at, id)` with the accepted eight-table metadata surface unchanged;
- configurable batch size, max attempts, retry base/max delay and stale-processing timeout policy with safe defaults and validation;
- due-only deterministic oldest-first claiming with short committed transactions and PostgreSQL `FOR UPDATE SKIP LOCKED` for concurrent workers;
- immutable non-PII claim descriptors containing outbox/application/event identity and incremented attempt generation only;
- guarded success/failure transitions requiring exact `id + status=processing + attempts=attempt_number`, preventing stale workers from mutating a newer claim generation;
- `sent` as terminal successful state and `failed` as terminal exhausted/permanent-failure state, while retryable work returns to `pending` with deterministic bounded exponential backoff;
- bounded stale `processing` recovery, requeueing below max attempts and terminally failing at max attempts;
- closed machine-safe failure codes only in `last_error`, with arbitrary raw exception/PII/secret strings rejected;
- claim/state transactions remain separate from future external delivery, so no database transaction will be held open during SMTP I/O;
- candidate intake remains unchanged: one candidate + three consents + one `pending`, attempts=0 outbox row in one transaction, with new delivery-state fields null initially;
- explicit at-least-once delivery semantics: a future SMTP accept followed by process death before `sent` persistence may cause a duplicate retry; no false exactly-once guarantee is claimed.

Final reported quality gate from `backend/`:
- 247 pytest tests passed, 1 skipped;
- 14 pre-existing Starlette `TestClient` deprecation warnings remained, with no new D1 warnings;
- Ruff passed.

#### Stage 4.4D2 - SMTP delivery and worker execution

Status: accepted.

Implemented:
- worker-only environment-backed SMTP settings with `SecretStr` password handling and safe defaults for port, STARTTLS mode, timeout and notification recipient;
- ordinary FastAPI settings/startup remain valid without SMTP configuration; complete delivery configuration is validated only when the worker command runs;
- validated SMTP sender/recipient headers, paired optional credentials and trusted `SITE_BASE_URL`, with HTTPS required outside local/dev/test and no credential/query/fragment URLs;
- immutable candidate notification snapshots built entirely inside a short database session from the persisted candidate and required consent rows;
- UTF-8 `text/plain` + escaped `text/html` administrator notifications with Moscow-time receipt display and a non-PII subject containing only the internal application ID;
- candidate-supplied values remain body content only and are never used as `From`, `To`, `Reply-To`, CC or BCC headers;
- candidate photographs are never attached/read for email delivery and private storage keys/paths are not exposed; notifications link only to the authenticated `/admin/candidates/{application_id}` page;
- stdlib `smtplib` transport with `ssl.create_default_context()`, verified STARTTLS or SMTP SSL, optional authenticated login and finite network timeout;
- SMTP/network failures classified into temporary/permanent internal delivery exceptions without propagating provider response text;
- one finite `process-email-outbox` execution cycle: validate configuration -> recover stale rows -> claim committed batch -> load immutable snapshot -> close DB session -> render/send outside DB transaction -> guarded sent/failure transition in a new short DB session;
- accepted D1 retry/backoff/state-generation logic remains authoritative; D2 does not duplicate claim/retry persistence behavior;
- recovery/claim/snapshot/transition persistence failures are translated to generic worker errors, while malformed settings/worker configuration produce safe CLI exit code 1 without tracebacks or rejected values;
- SMTP-accepted followed by failed `sent` persistence deliberately leaves the row `processing` for stale recovery and does not record a delivery failure or immediately resend; at-least-once duplicate risk remains explicit;
- one-shot worker only: no daemon loop, startup hook, Redis, Celery, in-process polling or candidate-confirmation email;
- schema remains exactly eight tables with migrations ending at `20260823_0005`; no D2 migration or persistence expansion;
- tests use fake/monkeypatched transports only and make no live SMTP/network calls.

Final reported quality gate from `backend/`:
- 280 pytest tests passed, 1 skipped;
- 14 pre-existing Starlette `TestClient` deprecation warnings remained, with no new D2 warnings;
- Ruff passed.

Deferred beyond D2:
- production scheduling/service integration such as systemd timer, cron or equivalent deployment mechanism;
- real production SMTP credential provisioning and connectivity verification;
- optional candidate confirmation email;
- public candidate-form activation until legal and deployment/security prerequisites are satisfied.

No public registration and no complex RBAC in MVP.

Post-backend frontend integration status:
- guarded public candidate-form integration is accepted;
- `VITE_CANDIDATE_FORM_ENABLED=false` is the fail-closed frontend default;
- the form matches the accepted multipart field/consent/photo/honeypot contract and uses the exact Saint Petersburg acknowledgement;
- no candidate PII is persisted in browser storage, cookies or URLs by the form integration;
- the backend gate `CANDIDATE_INTAKE_ENABLED=false` remains unchanged and authoritative for route registration.

Before candidate intake activation also complete:
- approved privacy-policy and personal-data-consent text/version identifiers;
- deployment request-body limits at Nginx/ASGI boundary;
- trusted proxy/client-IP configuration for production rate limiting;
- production SMTP credentials/connectivity and an explicit external schedule for `process-email-outbox`;
- end-to-end deployment/security acceptance with both frontend and backend gates enabled only in the approved environment.

## Review rule

Each Stage 4 slice gets its own branch and review before merge. Do not mix candidate security work, admin authentication and unrelated infrastructure changes into the same large pull request.
