# Astrea Production Preflight and Smoke Checks

These checks are for the public informational launch with candidate intake disabled. They do not activate mail, candidate intake, legal versions or any destructive operation.

## Preflight before starting the production stack

Run on the VPS as root or via sudo after `/etc/astrea/astrea.env` has been created and permissions set to `0600`:

```bash
cd /opt/astrea/current
sudo sh infra/host/production-preflight.sh /opt/astrea/current /etc/astrea/astrea.env
```

The preflight script checks without printing secret values:

- production env file exists, is not a symlink, is root-owned and mode `0600` when GNU `stat` is available;
- Docker and Docker Compose v2 are available;
- `APP_ENV=production`;
- PostgreSQL password is present, at least 20 characters and not a template value;
- `VITE_PUBLIC_SITE_ORIGIN` is one bare HTTPS origin and no template placeholder remains;
- Docker edge/proxy/backup values are present;
- both candidate activation gates are exactly `false`;
- normal and ops Compose configurations pass `docker compose config -q`.

The script intentionally does not print the environment file or expanded Compose configuration.

## Production sitemap behavior

The frontend production build now generates `dist/sitemap.xml` only when `VITE_PUBLIC_SITE_ORIGIN` is a valid public bare HTTPS origin. The same build appends the absolute sitemap URL to the generated `robots.txt`.

Fail-safe behavior is intentional:

- empty, localhost, `.local`, HTTP, credential-bearing or path/query/fragment origins do not produce a sitemap;
- the source `frontend/public/robots.txt` remains origin-neutral;
- the build-time sitemap contains only deterministic public routes whose indexability does not depend on managed publication state;
- unpublished managed pages and dynamic news detail URLs are not guessed or advertised by the static build;
- `/admin`, `/api/` and `/healthz` are never included.

Published managed pages and news articles remain discoverable through public navigation and their accepted publication-aware canonical/indexability behavior. A future dynamic sitemap extension should query only the published public-content boundary rather than enumerate drafts/placeholders.

## Smoke after HTTPS cutover

After the final hostname has a valid certificate and host Nginx is serving HTTPS, run from a network outside the VPS when possible:

```bash
sh infra/host/production-smoke.sh https://YOUR-PRODUCTION-HOSTNAME
```

The smoke script is read-only apart from ordinary HTTP requests. It verifies:

- public root returns 200 over HTTPS;
- HSTS and accepted CSP/security headers are present;
- web and backend health endpoints return the expected healthy response;
- admin shell is `noindex`;
- unauthenticated admin API access returns 401;
- unauthenticated private candidate-photo access returns 401;
- candidate intake endpoint returns 404 while the backend activation gate is disabled;
- `robots.txt` blocks admin/API/health paths and advertises the exact production sitemap URL;
- `sitemap.xml` is served, uses the final production origin and contains no admin/API paths;
- representative public routes return 200.

It does not log in, create content, create a candidate application, send email or modify database state.

## Required result before public acceptance

The deployment is not accepted until both commands finish with `ALL CHECKS PASSED` / `PASS` results and the operator has separately confirmed:

- `db`, `backend` and `web` are healthy and `migrate` exited 0;
- the initial administrator was bootstrapped successfully;
- bootstrap credentials were removed from the production env after bootstrap;
- Docker edge gateway/IP values match the trusted proxy contract;
- host Nginx passes `nginx -t`;
- production `robots.txt` and `sitemap.xml` point to the final HTTPS origin;
- backup directory is provisioned and a manual backup has been created successfully;
- candidate and email-worker activation remain disabled.

A restore is not part of the smoke procedure. Production restore remains a separately approved destructive operation.
