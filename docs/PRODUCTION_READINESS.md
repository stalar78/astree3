# Astrea Production Release Readiness

Status: repository preparation for the public informational launch. Real VPS execution, DNS changes, certificate issuance and cutover are performed only after the production host/domain are known and verified.

This release keeps the candidate workflow fail-closed. Public deployment does **not** require SMTP or candidate activation.

## 1. Release topology

The supported Stage 5.5 topology is:

```text
Internet
  -> host Nginx :80/:443 (TLS, redirect, HSTS, authoritative public client address)
    -> Docker edge network -> web Nginx
      -> backend FastAPI
        -> internal PostgreSQL network
```

Important boundaries:

- PostgreSQL is never host-published.
- FastAPI port 8000 is never host-published.
- the application `web` service remains published only on `127.0.0.1:${ASTREA_HTTP_PORT}` for local operator diagnostics;
- the host Nginx should proxy to the fixed `web` address on the Docker edge network, normally `172.30.250.10:80`;
- host Nginx is the only public listener on ports 80/443;
- TLS/HSTS live at the host Nginx layer; application CSP and the remaining response-security headers remain at the container Nginx layer.

The host template is `infra/host/astrea-nginx.conf.example`.

## 2. Trusted proxy chain

Production adds one reverse proxy in front of the already accepted container Nginx, so the client-IP chain must be explicit rather than implicitly trusting all forwarded headers.

The default production network contract is:

```text
ASTREA_EDGE_SUBNET=172.30.250.0/24
ASTREA_HOST_PROXY_IP=172.30.250.1
ASTREA_PROXY_IP=172.30.250.10
```

Meaning:

- `ASTREA_HOST_PROXY_IP` is the Linux host/gateway address as seen by the `web` container;
- `web` trusts `X-Real-IP` only from that address;
- host Nginx must overwrite `X-Real-IP` and `X-Forwarded-For` with its own `$remote_addr`, never append an incoming client chain;
- `web` then overwrites forwarding headers again before calling FastAPI;
- Uvicorn trusts proxy headers only from `ASTREA_PROXY_IP`, which is the fixed `web` container address.

Before cutover, verify the real Docker gateway rather than assuming `.1`:

```bash
docker network inspect astrea_edge --format '{{(index .IPAM.Config 0).Gateway}}'
```

The output must exactly equal `ASTREA_HOST_PROXY_IP` in `/etc/astrea/astrea.env`.

Verify the `web` container address:

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{if eq .NetworkID ""}}{{else}}{{.IPAddress}}{{end}}{{end}}' "$(docker compose --env-file /etc/astrea/astrea.env -f infra/compose.yml -p astrea ps -q web)"
```

If the chosen edge subnet collides with an existing VPS/VPN/container network, select a different private subnet and update all three related values plus the host Nginx upstream before deployment.

## 3. Host prerequisites

Baseline target: current supported Linux VPS with root/sudo access.

Required before deployment:

- Docker Engine with the Docker Compose v2 plugin;
- Git;
- host Nginx;
- an ACME/TLS client or provider certificate workflow (Certbot is acceptable);
- valid DNS A/AAAA routing for the selected production hostname;
- working time synchronization;
- outbound package/Docker registry access during deployment;
- sufficient persistent disk for PostgreSQL, private media, images and `/var/backups/astrea`.

Public firewall exposure should be limited to:

- SSH operator port;
- TCP 80;
- TCP 443.

Do not publish PostgreSQL 5432, FastAPI 8000 or the loopback application port to the Internet.

## 4. Production environment contract

Use `infra/production.env.example` as the safe template. The real file belongs outside Git, recommended path:

```text
/etc/astrea/astrea.env
```

Recommended permissions:

```bash
sudo chown root:root /etc/astrea/astrea.env
sudo chmod 0600 /etc/astrea/astrea.env
```

Never paste the real file into GitHub, issue comments, CI variables visible in logs, documentation or chat transcripts.

Required launch values:

- `APP_ENV=production` — required so admin cookies are `Secure`;
- `POSTGRES_PASSWORD` — long random production-only secret;
- `VITE_PUBLIC_SITE_ORIGIN` — exact bare HTTPS origin, for example `https://example.org`, no path/query/trailing slash;
- `ASTREA_EDGE_SUBNET`, `ASTREA_HOST_PROXY_IP`, `ASTREA_PROXY_IP` — verified production proxy/network values;
- `ASTREA_BACKUP_ROOT=/var/backups/astrea`;
- `ADMIN_INITIAL_USERNAME` and `ADMIN_INITIAL_PASSWORD` — temporary bootstrap credentials used only by the one-shot bootstrap service.

For the informational launch these values must remain exactly disabled:

```text
VITE_CANDIDATE_FORM_ENABLED=false
CANDIDATE_INTAKE_ENABLED=false
```

The legal version identifiers may remain empty while candidate intake is disabled.

SMTP variables may remain empty while candidate intake/mail are frozen. Do not enable the email-worker timer until live SMTP readiness and the separate candidate/legal acceptance are complete.

## 5. Safe configuration validation

From the checked-out production release directory:

```bash
docker compose \
  --env-file /etc/astrea/astrea.env \
  -f infra/compose.yml \
  -p astrea \
  config -q
```

Use `config -q`, not plain `config`, because the latter can print interpolated secret values to the terminal/log.

Also validate the ops profile without starting it:

```bash
docker compose \
  --profile ops \
  --env-file /etc/astrea/astrea.env \
  -f infra/compose.yml \
  -p astrea \
  config -q
```

Before any public start, manually confirm that the real env file does not contain the repository placeholders (`replace-with-...` or `.invalid`).

## 6. Backup directory provisioning

Provision the real host backup path before the first backup:

```bash
cd /opt/astrea/current
sudo ASTREA_BACKUP_ROOT=/var/backups/astrea sh infra/host/provision-backup-dir.sh
```

Expected result:

- directory owned by uid/gid `10001:10001`;
- mode `0700`;
- no recursive ownership changes to parent directories.

## 7. First application start

The release checkout should be pinned to the reviewed `main` commit intended for deployment.

Build/start the ordinary runtime:

```bash
cd /opt/astrea/current

docker compose \
  --env-file /etc/astrea/astrea.env \
  -f infra/compose.yml \
  -p astrea \
  up -d --build
```

Normal startup consists of `db`, one-shot `migrate`, `backend` and `web`. The backend does not become ready unless the migration service completes successfully.

Inspect state without exposing secrets:

```bash
docker compose --env-file /etc/astrea/astrea.env -f infra/compose.yml -p astrea ps
```

Required state:

- `db`: healthy;
- `migrate`: exited 0;
- `backend`: healthy;
- `web`: healthy.

Local host checks before TLS cutover:

```bash
curl --fail --silent --show-error http://127.0.0.1:8080/healthz
curl --fail --silent --show-error http://127.0.0.1:8080/api/v1/health
```

## 8. Initial administrator bootstrap

`admin-bootstrap` is a profile-only, one-shot service. Bootstrap credentials are not injected into the long-running backend service.

Run once after migrations are healthy:

```bash
docker compose \
  --profile ops \
  --env-file /etc/astrea/astrea.env \
  -f infra/compose.yml \
  -p astrea \
  run --rm admin-bootstrap
```

The command is idempotent in the accepted model: if an admin already exists, it reports the existing account instead of creating another one.

After a successful initial bootstrap, remove `ADMIN_INITIAL_USERNAME` and `ADMIN_INITIAL_PASSWORD` from the real environment file, then rerun `docker compose ... config -q`. They are not required for ordinary runtime.

## 9. Host Nginx and TLS

The final host config is based on `infra/host/astrea-nginx.conf.example`.

Before installation:

1. replace `__ASTREA_DOMAIN__` with the approved production hostname;
2. replace `__ASTREA_WEB_UPSTREAM__` with the verified `web` edge address, normally `172.30.250.10:80`;
3. provision a valid certificate/key using the chosen host/provider ACME process;
4. confirm the certificate paths used by the template exist;
5. run `nginx -t` before reload.

The host proxy deliberately overwrites client forwarding headers and sends a single authoritative client address. Do not replace that behavior with `$proxy_add_x_forwarded_for` without a new security review.

The host template redirects HTTP to HTTPS and emits:

```text
Strict-Transport-Security: max-age=31536000
```

Install the final HSTS-enabled config only after a valid HTTPS endpoint is confirmed. HSTS is intentionally not emitted by the inner HTTP-only container Nginx.

After installing the site config:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Then verify from an external network, not only localhost.

## 10. Candidate/mail freeze during public launch

The public information site can be deployed while candidate intake remains disabled.

Launch requirements:

- `/vstuplenie` may render the accepted informational/disabled form presentation;
- frontend submission gate remains `false`;
- backend candidate route remains unregistered because `CANDIDATE_INTAKE_ENABLED=false`;
- SMTP readiness is not required for this launch;
- `astrea-ops-email-worker.timer` must not be enabled.

Candidate activation is a later explicit release requiring the already documented legal-version, SMTP and controlled acceptance prerequisites.

## 11. Operations installation after runtime acceptance

Create the host ops environment from `infra/systemd/astrea-ops.env.example` as:

```text
/etc/astrea/ops.env
```

It contains paths/settings, not application credentials. Recommended permissions are root-owned `0600`.

Install the reviewed service/timers only after manual backup succeeds. For the informational launch, enable only backup and prune schedules; do **not** enable the email-worker timer.

Example installation paths:

```bash
sudo install -m 0644 infra/systemd/astrea-ops@.service /etc/systemd/system/
sudo install -m 0644 infra/systemd/astrea-ops-backup.timer /etc/systemd/system/
sudo install -m 0644 infra/systemd/astrea-ops-prune.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

Before enabling timers, run the operations manually and inspect journald/output.

A production restore is destructive and is never part of routine deployment. Do not execute the restore path without a separate explicit approval and a confirmed backup identifier.

## 12. Cutover prerequisites

Do not switch public DNS until all of the following are true:

- reviewed release commit is checked out;
- all required GitHub CI gates are green;
- production env is root-owned/0600 and free of placeholders;
- both candidate activation gates are false;
- Compose config validates quietly;
- database migration exited 0;
- db/backend/web are healthy;
- initial admin bootstrap succeeded and bootstrap credentials were removed from the env file;
- host proxy IP and web proxy IP match the trusted-chain configuration;
- TLS certificate is valid for the final hostname;
- HTTP redirects to HTTPS;
- HTTPS carries HSTS and the accepted application security headers;
- public routes and admin login shell load through the final hostname;
- `/admin`, `/api/` and `/healthz` retain noindex response controls;
- backup path is provisioned and at least one validated pre-cutover backup exists where applicable;
- rollback target/current old site is preserved until acceptance completes.

## 13. Rollback rule

Before cutover, record:

- previous site/DNS target;
- deployed Astrea Git commit SHA;
- previous known-good Astrea commit SHA if this is an update;
- most recent validated backup ID.

For an application-only regression with a migration-compatible schema, return to the prior reviewed commit and rebuild/restart the stack.

If rollback requires database/private-media state reversal, stop and use the explicit reviewed restore procedure only with separate destructive approval. Never improvise a database downgrade or delete named Docker volumes during rollback.

For the first cutover from the legacy site, keep the legacy deployment intact until the new hostname/DNS path is accepted.

## 14. External inputs still required for actual deployment

Repository work can complete without secrets, but the real deployment still needs these external facts from the operator/client:

- VPS public IP/hostname and SSH access method;
- final production domain/subdomain;
- DNS provider/control path;
- chosen TLS certificate/renewal method on that VPS.

SMTP/service-mailbox information is **not** required for the informational launch because candidate intake remains disabled.
