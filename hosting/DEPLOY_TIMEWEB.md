# Astrea HOSTING — Timeweb deployment runbook

This runbook is for the H5 shared-hosting package. It prepares and validates a deployable artifact but does **not** authorize a production deployment by itself.

## 1. Build the upload artifact

Use Node.js 22 and install the locked frontend dependencies first:

```bash
npm --prefix frontend ci
node hosting/scripts/build-package.mjs --origin=https://YOUR-DOMAIN.EXAMPLE
```

The origin must be the final bare HTTPS origin. The builder generates the HOSTING frontend, sitemap and robots metadata and writes:

```text
hosting/release/astrea-hosting/
  public/                 # web document root only
    index.html
    assets/
    brand/
    media/
    api/
    editor/
    .htaccess
    robots.txt
    sitemap.xml
  private/                # must stay outside public_html
    config/
    db/
    scripts/
  DEPLOY_TIMEWEB.md
  manifest.json
```

Never put a real `config.local.php` in Git or in a build artifact.

## 2. Keep private files outside `public_html`

Timeweb virtual hosting uses Nginx in front of Apache for static files. Static files can be served by Nginx without Apache `.htaccess` rules. Therefore SQL dumps, configuration files, backups and operator scripts must not be placed under the public document root and must not rely on `.htaccess` for secrecy.

The recommended account layout is:

```text
~/SITE_DIRECTORY/
  public/
  private/
  public_html -> public
```

Timeweb documents this `public_html` symlink pattern for frameworks with a separate public directory. If the site already exists, take a backup before changing its document-root layout. With SSH, a typical cutover is conceptually:

```bash
cd ~/SITE_DIRECTORY
mv public_html public_html.before-astrea
ln -s "$PWD/public" public_html
```

Do not run those commands blindly against an existing production directory. Confirm the actual Timeweb site directory first.

## 3. Select PHP and run the capability preflight

Use a current PHP 8.x version. The supported Astrea HOSTING baseline is PHP 8.2 or newer; PHP 8.4 is the preferred Timeweb target unless the account has a different approved current version.

Timeweb allows a site PHP version to be selected in the hosting panel and exposes versioned CLI binaries under `/opt/phpXX/bin/php`.

Before installing credentials or schema:

```bash
/opt/php84/bin/php private/scripts/preflight.php
```

The preflight verifies the required PHP/PDO extensions and reports the account's relevant runtime limits, including:

- `upload_max_filesize`;
- `post_max_size`;
- `memory_limit`;
- `max_execution_time`;
- `max_input_vars`;
- optional `fileinfo`, `gd` and `imagick` availability.

The optional upload-related values are recorded for a future upload slice. Binary editorial upload is not enabled by the current H5 package.

## 4. Create and initialize MySQL

Create a MySQL database in the Timeweb panel. For a local Timeweb database the host is `localhost` (or `127.0.0.1`) and the database username is the database name.

Apply the schema in order. The `-p` flag intentionally has no password value so the password is prompted and does not enter shell history:

```bash
mysql -u DB_NAME DB_NAME -p < private/db/001_initial.sql
mysql -u DB_NAME DB_NAME -p < private/db/002_editor_auth.sql
```

The same SQL files may be imported in phpMyAdmin if SSH/CLI import is not convenient. Both migrations are designed to be safe for the intended re-application checks.

## 5. Install private configuration

Create the real configuration only on the hosting account:

```bash
cp private/config/config.local.php.example private/config/config.local.php
chmod 600 private/config/config.local.php
```

Edit `private/config/config.local.php` and set the actual database values. The intended local Timeweb DSN is:

```text
mysql:host=localhost;dbname=DB_NAME;charset=utf8mb4
```

Keep the production editor session settings secure:

```text
secure = true
same_site = Strict
```

The runtime first looks for `<site>/private/config/config.local.php`; the source-tree `hosting/config/config.local.php` location remains only a local/CI compatibility path.

## 6. Verify configuration and schema

After the private config and SQL schema are installed, run:

```bash
/opt/php84/bin/php private/scripts/preflight.php --check-db
```

This adds a real database connection check and verifies the required tables plus migration markers `001_initial` and `002_editor_auth`.

## 7. Create the one Lite Editor account

The bootstrap is intentionally CLI-only and refuses to create a second editor account. The password is read from standard input and never accepted as a command-line argument.

A shell-safe pattern that also avoids showing the password while typing is:

```bash
read -s -p "Editor password: " ASTREA_EDITOR_PASSWORD; echo
printf '%s\n' "$ASTREA_EDITOR_PASSWORD" | /opt/php84/bin/php private/scripts/bootstrap-editor.php astreaadmin
unset ASTREA_EDITOR_PASSWORD
```

Use a unique password of at least 14 characters. Do not put it in the command itself, a repository file or a chat/log transcript.

## 8. HTTPS, domain and SEO

Before public acceptance:

1. bind the final domain to the Timeweb site;
2. install/enable SSL and verify HTTPS works;
3. confirm the package was built with that exact HTTPS origin;
4. verify `sitemap.xml` and `robots.txt` contain the final domain;
5. keep the editor session `secure=true`.

Changing editorial content does **not** require a frontend rebuild. Changing the production site origin/domain does require rebuilding the static package so canonical sitemap/robots metadata stays correct.

## 9. Smoke checklist

Run the following against the technical/final domain before production acceptance.

### Public routing

- `/` loads the accepted Astrea frontend;
- deep links such as `/materialy`, `/novosti`, `/video`, `/kontakty`, `/faq` load directly without a 404;
- assets under `/assets`, `/brand` and `/media` load;
- `/api/health` and `/api/v1/health` return success;
- `/editor/` opens the Lite Editor login and is not indexable;
- a request for `/private/...` or `/config/...` never returns private file contents.

### Content isolation

- create a draft News record: it must not appear publicly;
- publish it: it appears under `/novosti`;
- unpublish it: it disappears publicly;
- publish one book/article/video material: it appears under `/materialy` in the expected group;
- publish an event in the visible range: the desktop calendar marks the date and mobile/tablet shows it in “Ближайшие события”;
- the existing `/video` page still renders only approved RuTube video materials.

### Security boundaries

- wrong editor password produces only a generic failure;
- repeated failed logins trigger throttling;
- logout invalidates the editor session;
- state-changing editor forms reject a missing/invalid CSRF token;
- `/api/v1/candidate-applications` remains absent in HOSTING;
- no Admin route or API namespace is exposed as an authorization substitute;
- `private/`, SQL files, backups and real credentials are physically outside `public_html`.

### SEO/origin

- `sitemap.xml` contains the final HTTPS origin;
- `/admin`, `/editor` and `/api` are absent from the sitemap;
- `robots.txt` references the final sitemap;
- public managed pages/news produce the expected document titles/descriptions after publication.

## 10. Backup and export

Timeweb provides automatic database backups, but take an explicit backup before every schema/runtime cutover.

A manual MySQL dump over SSH can be created without placing the password in shell history:

```bash
mkdir -p ~/astrea-backups
mysqldump -u DB_NAME DB_NAME -p --no-tablespaces > ~/astrea-backups/astrea-$(date +%Y%m%d-%H%M%S).sql
```

The same database can be exported through phpMyAdmin. Keep dumps under the account home/private backup area, never under `public`/`public_html`.

Also retain a copy of the currently deployed `public` and `private` directories before replacing runtime files. Treat the private config and any future uploaded media as backup-sensitive data.

Restore rehearsal for H5 should prove that a clean database can accept the SQL schema or a saved dump and that the public/editor health checks still pass afterward.

## 11. H5 production acceptance gate

Before any real production cutover, record the actual account values/results for:

- selected PHP version and required extensions;
- MySQL server version and successful schema preflight;
- `upload_max_filesize`, `post_max_size`, `memory_limit` and execution limits;
- `public_html -> public` (or equivalent) document-root behavior;
- Apache rewrite handling for SPA/API/editor requests;
- HTTPS and final site origin;
- public/editor smoke checklist;
- backup/export success.

H5 packaging and CI can be completed without production access. The final account-specific validation and deployment are separate operational actions and require explicit approval.
