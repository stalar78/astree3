# Project Blueprint: Astrea

Current stage: Stage 1 - Architecture & Design System

## Purpose

Build a new official public website for Astrea with manageable content and a secure candidate application workflow.

## Users

Primary public users:
- Visitors interested in the lodge
- Potential candidates

Internal user:
- Site administrator

## Success Criterion

A production-ready site passes the approved acceptance criteria, including a complete end-to-end candidate application: form -> validation -> secure persistence -> admin availability -> email notification.

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
- Dashboard
- News management
- Video management
- Editable allowed page content
- Candidate application list/details/statuses

Candidate application:
- Form
- Photo upload
- Consent checkboxes
- Server-side validation
- Anti-spam protection
- Database persistence
- Private photo storage
- Structured email notification

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

Email worker -> SMTP / email provider
Video pages -> approved external provider URLs, primarily RuTube
```

Key decisions:
- PostgreSQL is the source of truth for candidate applications.
- Candidate data is persisted before email delivery is attempted.
- Candidate photos are private and never served as an open static directory.
- Email delivery uses a persistent outbox and retryable worker.
- Admin authentication uses secure server-side/session-cookie semantics; no privileged token storage in browser localStorage.
- External video embeds are provider/domain allowlisted.
- MVP stays a modular monolith; no Redis/Celery/microservices unless later justified.

## Design Direction

Detailed design baseline: `docs/DESIGN_SYSTEM.md`.

Brand source: client Jubilee Repository, especially pages 4-5.

Official palette references:
- Pantone 485 C - red accent
- Pantone Cool Gray 6 C
- Pantone Cool Gray 10 C
- Pantone Process Black C
- White

Working screen approximations are defined in `docs/DESIGN_SYSTEM.md`; Pantone remains the brand source of truth.

Direction:
- classical;
- restrained;
- status-oriented;
- editorial/historical rather than SaaS;
- slightly traditional/old-fashioned is acceptable;
- no generic occult styling;
- no excessive animation;
- hero uses the client-supplied Astrea standard on a dark background with subtle backlighting.

Typography direction: classical Cyrillic-capable serif/antiqua for headings plus a highly readable Cyrillic-capable body/UI face. Final families are selected during prototype review.

## Security

Main security risk: candidate forms contain personal data and photos.

Security requirements:
- HTTPS
- Private candidate data
- Non-public candidate photos
- Authenticated admin
- Secrets only through environment variables
- Backup policy
- Server-side validation
- Upload validation and image normalization
- Anti-spam/rate limiting
- Persistent consent records
- No production write access for agents without explicit approval

The `religion` field remains disabled until the client approves the legal wording and processing basis for special-category personal data.

## Current Next Steps

1. Review/merge Stage 1 architecture and design baseline.
2. Prepare Lovable prompt for the public-site visual prototype.
3. Build and review the Home page visual direction first.
4. Extend the approved system to internal public pages, news, video and candidate form.
5. Scaffold application code only after visual direction is accepted.
