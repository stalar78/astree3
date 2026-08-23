# Stage 4 Backend Plan

Status: in progress. Stage 4.1, Stage 4.2, Stage 4.3, Stage 4.4A, Stage 4.4B and Stage 4.4C accepted; Stage 4.4D is next.

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

Activation remains deliberately deferred until approved privacy/consent documents, frontend wiring and deployment/security review are complete.

## Stage 4.4 - Admin and operations

Status: in progress. Stage 4.4A, Stage 4.4B and Stage 4.4C accepted; Stage 4.4D is next.

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
- `401` redirects to login while write `403` remains in the editor with the accepted session-security message;
- mutation errors keep current in-memory form values visible/editable and are never automatically retried;
- explicit retry controls for temporary/network list and detail GET failures;
- generic user-facing mutation/load errors without displaying raw backend response detail;
- unpublished editorial draft state kept only in React component memory: no `localStorage`, `sessionStorage`, IndexedDB, cookies, URL content payloads, console logging or autosave;
- no public-site changes and no new frontend dependencies.

Final reported quality gate from `frontend/`:
- `npm run typecheck` passed;
- `npm run lint` passed;
- `npm run build` passed.

### Stage 4.4D - Email outbox operations

Status: next.

Implement:
- persistent outbox worker;
- SMTP/provider delivery;
- retry/status transitions;
- bounded error recording without secrets/PII leakage;
- no Redis/Celery unless later justified.

No public registration and no complex RBAC in MVP.

Before candidate intake activation also complete:
- approved privacy-policy and personal-data-consent text/version identifiers;
- public frontend candidate-form integration;
- deployment request-body limits at Nginx/ASGI boundary;
- trusted proxy/client-IP configuration for production rate limiting.

## Review rule

Each Stage 4 slice gets its own branch and review before merge. Do not mix candidate security work, admin authentication and unrelated infrastructure changes into the same large pull request.
