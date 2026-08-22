# Stage 4 Backend Plan

Status: in progress. Stage 4.1, Stage 4.2, Stage 4.3 and Stage 4.4A accepted; Stage 4.4B is next.

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

Status: in progress. Stage 4.4A accepted; Stage 4.4B is next.

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

Status: next.

Implement:
- authenticated candidate list;
- authenticated candidate detail;
- constrained candidate status workflow;
- authenticated private-photo access;
- no public candidate data/photo routes;
- reuse Stage 4.4A auth and CSRF dependencies for state-changing operations.

### Stage 4.4C - Content administration

Implement:
- authenticated CRUD for news;
- authenticated CRUD for external videos;
- constrained editing of approved page content;
- no arbitrary page-builder/layout mutation.

### Stage 4.4D - Email outbox operations

Implement:
- persistent outbox worker;
- SMTP/provider delivery;
- retry/status transitions;
- bounded error recording without secrets/PII leakage;
- no Redis/Celery unless later justified.

No public registration and no complex RBAC in MVP.

Before candidate intake activation also complete:
- approved privacy-policy and personal-data-consent text/version identifiers;
- frontend candidate-form integration;
- deployment request-body limits at Nginx/ASGI boundary;
- trusted proxy/client-IP configuration for production rate limiting.

## Review rule

Each Stage 4 slice gets its own branch and review before merge. Do not mix candidate security work, admin authentication and unrelated infrastructure changes into the same large pull request.
