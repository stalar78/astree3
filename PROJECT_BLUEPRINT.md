# Project Blueprint: Astrea

Current stage: Stage 0 - Initialization

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

## High-Level Architecture

Visitor/Admin
   -> React UI
   -> FastAPI
   -> PostgreSQL
   -> private file storage

FastAPI
   -> email provider / SMTP

Public video pages
   -> external video provider URLs, primarily RuTube

## Design Direction

- Classical
- Restrained
- Status-oriented
- Deliberately slightly traditional/old-fashioned is acceptable
- No futuristic SaaS aesthetic
- No excessive animation

Official brand palette source: client Jubilee Repository, pages 4-5.

Palette references:
- Pantone 485 C - red accent
- Pantone Cool Gray 6 C
- Pantone Cool Gray 10 C
- Pantone Process Black C
- White

Do not invent HEX conversions yet. Web color tokens will be calibrated during the design-system stage.

Hero direction: Astrea standard on a dark background with subtle backlighting.

Typography direction: classical serif / antiqua feeling for headings, highly readable Cyrillic-compatible text face for body copy. Exact fonts are not decided yet.

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
- Upload validation
- Anti-spam/rate limiting
- No production write access for agents without explicit approval

## Current Next Steps

1. Complete project bootstrap.
2. Create Idea-stage project memory.
3. Architecture stage.
4. Design-system specification.
5. Lovable design prototype.
6. Review and approval.
7. Application scaffolding.
