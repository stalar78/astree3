# Stage 4 Backend Plan

Status: in progress. Stage 4.1 accepted; Stage 4.2 is next.

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

Status: next.

Implement structured persistence/API for:
- pages;
- news posts;
- external videos.

Requirements:
- draft/published state where applicable;
- stable news slugs;
- approved external video URLs only;
- provider/domain allowlist, initially focused on RuTube;
- no arbitrary iframe HTML;
- public read endpoints separated from future admin writes.

## Stage 4.3 - Candidate intake and private media

Treat as a security-sensitive transaction.

Required flow:

```text
multipart request
 -> authoritative server validation
 -> anti-spam/rate-limit checks
 -> image decode/validation/normalization
 -> private generated file identity
 -> single DB transaction:
      candidate application
      consent records
      email outbox row
 -> success response
```

Rules:
- PostgreSQL is the source of truth;
- accepted applications are persisted before email is attempted;
- failed email cannot lose an application;
- private photographs remain outside the public web root;
- original upload filenames are not storage identifiers;
- actual image decoding is required, not extension-only validation;
- normalize/re-encode images and strip unnecessary metadata;
- consent records capture type, timestamp and document/policy version;
- `religion` remains disabled pending separate legal approval.

## Stage 4.4 - Admin and operations

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

## Review rule

Each Stage 4 slice gets its own branch and review before merge. Do not mix candidate security work, admin authentication and unrelated infrastructure changes into the same large pull request.
