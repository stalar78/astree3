# Client Demo in GitHub Codespaces

Status: implementation available; live Codespaces smoke acceptance is still required before this workflow is marked accepted in the project blueprint.

## Purpose

This environment is for temporary client review before production deployment. It runs the real Astrea application stack in an isolated GitHub Codespace:

```text
GitHub Codespaces forwarded HTTPS URL
  -> Nginx
     -> React frontend
     -> FastAPI
        -> PostgreSQL
```

It is not production deployment and must not contain real candidate or production data.

## Safety baseline

- the Codespaces forwarded port starts private;
- public access is enabled only by an explicit `share` command;
- candidate frontend and backend activation gates remain `false`;
- no legal version identifiers are configured;
- no SMTP credentials or mail worker are configured;
- `VITE_PUBLIC_SITE_ORIGIN` remains empty, so the temporary Codespaces URL is not emitted as a production canonical;
- PostgreSQL and backend ports remain internal to the existing Compose topology;
- a fresh demo database is isolated under Compose project `astrea-demo`;
- a disposable `demo_admin` password and PostgreSQL password are generated locally inside the Codespace and written only to ignored `infra/.env.codespaces.local` with mode `0600`.

Do not paste real credentials, candidate data, client secrets or production backups into the Codespace.

## Start a demo

From the repository page:

1. Open **Code -> Codespaces**.
2. Create a codespace from `main`.
3. Wait for the devcontainer `postCreateCommand` to finish. The initial Docker build can take several minutes.
4. In the terminal, verify the stack:

```bash
bash .devcontainer/demo.sh status
```

The demo script uses the existing `infra/compose.yml`; it does not maintain a second application topology.

## Share with the client

The forwarded port is private by default. When you are ready to demonstrate the site, run:

```bash
bash .devcontainer/demo.sh share
```

The command changes only Codespaces port `18080` to public visibility and prints:

- the temporary client URL;
- `/admin/login` URL;
- the disposable `demo_admin` username;
- the disposable demo-admin password.

A public Codespaces port is accessible to anyone who knows its URL. Send the URL and demo credentials only to the intended reviewers.

The client can review the public site and use the real protected administration UI for Pages, News and Video. A fresh demo database contains the predefined managed pages in their normal unpublished seed state; client/demo edits stay inside this disposable Codespace database.

## Close access

As soon as the review session is finished, run:

```bash
bash .devcontainer/demo.sh private
```

This returns port `18080` to private visibility. GitHub Codespaces also reverts a public forwarded port to private when the port is removed/re-added or the codespace restarts, but the explicit `private` command is the normal close-out action.

## Other commands

```bash
bash .devcontainer/demo.sh up
bash .devcontainer/demo.sh credentials
bash .devcontainer/demo.sh status
```

`up` is idempotent: it rebuilds/starts the existing demo Compose project and ensures the initial `demo_admin` exists. Existing demo content remains in the Codespace Docker volumes.

## Deliberate exclusions

This workflow does not:

- deploy anything to a VPS;
- change the protected `main` release/runtime model;
- enable candidate intake;
- send email;
- configure production domain/DNS/TLS;
- provision production secrets;
- seed fabricated client content or candidate applications;
- replace Stage 5.5 production deployment and acceptance.

## Acceptance still required

Before marking Client Demo as accepted, perform one controlled Codespaces run and verify:

- devcontainer creation completes;
- `astrea-demo` PostgreSQL/backend/web become healthy and migrations finish;
- the generated admin can log in through the forwarded HTTPS URL;
- Pages/News/Video administration works against only the demo database;
- candidate intake remains unavailable;
- `share` makes only port `18080` public;
- `private` closes public access again.
