# Stage 2 Design Freeze

Status: approved.

Stage 2 public-site visual design is accepted as the implementation reference for the frontend.

## Approved prototype reference

Lovable project: `f210a612-2a9e-4c62-80d4-0f1d348734ad`

Approved Lovable commit: `1f6206f6f598c40af60796ee783430cbaf4837ff`

Preview: `https://id-preview--f210a612-2a9e-4c62-80d4-0f1d348734ad.lovable.app`

The implementation must preserve the approved visual character rather than reinterpret it.

## Approved public routes

- `/`
- `/o-lozhe`
- `/lozhi-sankt-peterburga`
- `/celi-i-principy`
- `/vstuplenie`
- `/faq`
- `/novosti`
- `/novosti/:slug`
- `/video`
- `/kontakty`
- `/privacy`
- `/consent`

## Visual baseline

The accepted genre is an official historical/institutional representation, not a commercial landing page.

Preserve:
- monumental, axial composition;
- dark official header and compact dark internal-page heroes;
- classical serif-led typography and restrained sans-serif utility text;
- large margins and narrow editorial text columns;
- paper / alternate-paper / dark section rhythm;
- thin rules and restrained ornament dividers;
- editorial/archive treatment for news and video rather than product cards;
- minimal animation and no SaaS visual language.

Avoid:
- sales/marketing layouts;
- excessive cards;
- generic occult/Masonic stock imagery;
- random gold symbols, candles, smoke, temples or invented heraldry;
- redesigning the approved hero into a text-left / image-right commercial layout.

## Official assets

Runtime public brand assets originate from the approved files already stored in `assets/brand/`:

- `grand-lodge-russia-emblem.png`
- `province-northwest-emblem.png`
- `astrea-standard-transparent.png`
- `astrea-seal.png`

Placement is fixed conceptually:
- top/header: Great Lodge of Russia and North-West Province emblems;
- home hero: Astrea standard;
- bottom/footer: Astrea seal.

Do not regenerate, recolor, crop or replace these assets.

## Content safety baseline

Do not invent history, dates, events, doctrine, ritual claims, organizational hierarchy, candidate requirements, news, videos, contacts or legal wording.

Confirmed public wording may include:
- D.L. Astrea No. 3 / Достопочтенная Ложа «Астрея» № 3;
- Saint Petersburg / «на Востоке Санкт-Петербурга»;
- official symbols supplied by the client;
- `MDCCLXXV` as a date/mark present on the official symbolism, without asserting an unsupported historical interpretation.

Where approved content is not yet available, use honest editorial empty states.

The `religion` field is not part of the public candidate form at this stage. It remains disabled pending separate legal review.

## Candidate-page design baseline

The approved `/vstuplenie` page is a visual prototype only. No data is stored or submitted in Stage 2.

The future form structure includes:
- identity/profile data;
- education;
- work / occupation;
- family status;
- membership in other organizations;
- VK / public social links;
- about / motivation text;
- JPG/PNG/WebP photo;
- required privacy/data-processing consents;
- explicit confirmation that the application is being submitted to a lodge working in Saint Petersburg.

Production implementation must keep candidate photos private and move all authoritative validation to FastAPI.

## Stage 3 implementation rule

The Lovable project is the visual source of truth, not the production architecture source of truth.

Production frontend remains the architecture defined in `.architecture/ARCHITECTURE.md`:
- `frontend/` directory;
- React + TypeScript + Vite + Tailwind;
- React Router;
- static frontend build served by Nginx;
- FastAPI backend under `/api/v1` later.

Therefore Stage 3 should port the approved visuals/components/routes into the planned frontend architecture instead of copying Lovable-specific runtime/server tooling blindly.

Do not introduce Supabase, Lovable backend services, TanStack Start/Nitro or unrelated shadcn dependencies merely because they exist in the prototype.

## Stage 3 acceptance gate

Before merge, the frontend implementation must demonstrate:
- visual parity with the approved Lovable prototype on desktop and mobile;
- all approved public routes working;
- one semantic `h1` per route;
- no broken internal links;
- no console errors;
- brand images served from project public assets;
- no backend submission from the candidate form yet;
- no fabricated content introduced during the port;
- production build and lint/type checks passing.
