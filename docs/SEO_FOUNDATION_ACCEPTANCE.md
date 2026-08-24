# SEO Foundation Acceptance

Status: **accepted** on 2026-08-24 after repository review, required CI and controlled local E2E verification.

## Accepted behavior

The frontend now has a fail-safe SEO baseline without inventing a production deployment origin:

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

## Acceptance evidence

PR #54 implemented the SEO foundation and passed the required `Backend`, `Frontend` and `PostgreSQL Integration` checks. Controlled local E2E then found one Nginx edge case: `/admin` lost its response-level robots header after SPA fallback because `$uri` changed to `/index.html`. PR #55 corrected the mapping to use the original request URI with query-safe patterns and again passed all three required checks.

The final `astrea-e2e` runtime verified:

- `/robots.txt` returns the expected public allow and service-path disallow rules;
- `/api/v1/health` and `/healthz` return `X-Robots-Tag: noindex, nofollow, noarchive`;
- `/admin` and `/admin?probe=1` both return the same noindex header after the SPA-fallback fix;
- `/` remains indexable and has no response-level noindex header;
- browser runtime on `/` reports `title = Astrea`, the accepted public description, `robots = index, follow` and no canonical on localhost;
- browser runtime on unpublished `/o-lozhe` reports `title = О ложе | Astrea`, `robots = noindex, nofollow, noarchive` and no canonical while the public page API returns `404`.

## Deliberate deferral

No sitemap is generated yet. Sitemap entries require absolute URLs, and the real production domain/subdomain is not approved. `VITE_PUBLIC_SITE_ORIGIN` must remain unset until that origin is known. Sitemap generation and production canonical activation are therefore a small Stage 5.5 follow-up rather than something to fake in local or repository defaults.

This acceptance does not alter candidate/legal activation, SMTP/mail configuration or production deployment status.
