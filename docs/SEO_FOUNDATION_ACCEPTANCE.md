# SEO Foundation Acceptance

Status: **accepted** on 2026-08-24 after repository review, required CI and controlled local E2E verification. Production sitemap readiness was added later as a fail-safe Stage 5.5 follow-up without inventing a deployment origin.

## Accepted behavior

The frontend has a fail-safe SEO baseline without inventing a production deployment origin:

- route-level title and description handling is centralized through the SEO helper;
- `VITE_PUBLIC_SITE_ORIGIN` is optional and empty by default;
- canonical links are emitted only when the configured origin is a valid bare, non-local HTTPS origin;
- localhost and other unapproved origins therefore do not receive a canonical URL;
- public news detail pages remain `noindex` while loading, missing or failed and become indexable only after a published article is returned by the public API;
- predefined managed pages remain `noindex` while loading, unpublished/missing or failed and become indexable only when published content is actually returned;
- published managed-page descriptions are derived from the stored published page text rather than placeholder copy;
- canonical paths normalize trailing slashes.

Crawler controls are also present at the static/Nginx boundary:

- `frontend/public/robots.txt` allows the public site and disallows `/admin`, `/api/` and `/healthz`;
- Nginx sends `X-Robots-Tag: noindex, nofollow, noarchive` for `/admin`, `/api/` and `/healthz`;
- the Nginx rule evaluates the original request URI so the header survives SPA fallback and remains correct for query-string variants such as `/admin?probe=1`;
- the public root does not receive the noindex response header.

## Production sitemap readiness

The production build runs `frontend/scripts/generate-sitemap.mjs` after the Vite build.

The generator intentionally mirrors the canonical-origin safety contract:

- a sitemap is generated only for a valid public bare HTTPS `VITE_PUBLIC_SITE_ORIGIN`;
- empty, localhost, `.local`, HTTP, credential-bearing and path/query/fragment origins produce no `dist/sitemap.xml`;
- when generated, the build also appends the exact absolute sitemap URL to the built `robots.txt`;
- the source `frontend/public/robots.txt` stays origin-neutral;
- the static sitemap contains only deterministic public routes whose indexability does not depend on publication state;
- unpublished managed pages and dynamic news detail URLs are not guessed at build time;
- admin, API and health paths are never included.

Published managed pages and news articles retain their publication-aware runtime SEO behavior and can be discovered through public navigation. If a future dynamic sitemap is added, it must query only the published public-content boundary and must not enumerate drafts/placeholders.

## Acceptance evidence

PR #54 implemented the SEO foundation and passed the required `Backend`, `Frontend` and `PostgreSQL Integration` checks. Controlled local E2E then found one Nginx edge case: `/admin` lost its response-level robots header after SPA fallback because `$uri` changed to `/index.html`. PR #55 corrected the mapping to use the original request URI with query-safe patterns and again passed all three required checks.

The final `astrea-e2e` runtime verified:

- `/robots.txt` returns the expected public allow and service-path disallow rules;
- `/api/v1/health` and `/healthz` return `X-Robots-Tag: noindex, nofollow, noarchive`;
- `/admin` and `/admin?probe=1` both return the same noindex header after the SPA-fallback fix;
- `/` remains indexable and has no response-level noindex header;
- browser runtime on `/` reports `title = Astrea`, the accepted public description, `robots = index, follow` and no canonical on localhost;
- browser runtime on unpublished `/o-lozhe` reports `title = О ложе | Astrea`, `robots = noindex, nofollow, noarchive` and no canonical while the public page API returns `404`.

The production sitemap follow-up adds CI coverage for both sides of the fail-safe contract: a valid HTTPS example origin must generate the expected sitemap/robots entries, while an invalid HTTP origin must remove the sitemap and origin advertisement. The post-TLS production smoke harness also verifies `/sitemap.xml` and the final `robots.txt` against the real production origin.

This acceptance does not alter candidate/legal activation or SMTP/mail configuration. Those remain separately frozen until explicitly resumed.
