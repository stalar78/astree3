# Stage 4 Backend Plan

Status: in progress. Stage 4.1, Stage 4.2 and Stage 4.3 accepted; Stage 4.4 is next.

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

Status: next.

Implement:
- closed admin authentication;
- secure password hashing;
- HttpOnly/Secure session-cookie model in production;
- CSRF protection for state-changing authenticated requests as required;
- candidate list/detail/status workflow;
- authenticated private-photo access;
- news/video/page administration;
- persistent email-outbox worker/retry handling.

No public registration and no complex RBAC in MVP.

Before candidate intake activation also complete:
- approved privacy-policy and personal-data-consent text/version identifiers;
- frontend candidate-form integration;
- deployment request-body limits at Nginx/ASGI boundary;
- trusted proxy/client-IP configuration for production rate limiting.

## Review rule

Each Stage 4 slice gets its own branch and review before merge. Do not mix candidate security work, admin authentication and unrelated infrastructure changes into the same large pull request.
