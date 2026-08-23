from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.admin_bootstrap import AdminBootstrapError, bootstrap_initial_admin
from app.services.email_worker import (
    EmailWorkerConfigurationError,
    EmailWorkerError,
    EmailWorkerPersistenceError,
    run_email_outbox_once,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="astrea-backend")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("bootstrap-admin", help="Create the initial admin user if needed.")
    subparsers.add_parser("process-email-outbox", help="Run one finite email outbox processing pass.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "bootstrap-admin":
        settings = get_settings()
        try:
            with SessionLocal() as db:
                result = bootstrap_initial_admin(db, settings)
        except AdminBootstrapError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        state = "created" if result.created else "exists"
        print(f"Admin user {state}: {result.username}")
        return 0

    if args.command == "process-email-outbox":
        settings = get_settings()
        try:
            result = run_email_outbox_once(settings, SessionLocal)
        except EmailWorkerConfigurationError:
            print("Email outbox configuration is invalid.", file=sys.stderr)
            return 1
        except (EmailWorkerPersistenceError, EmailWorkerError):
            print("Email outbox processing failed.", file=sys.stderr)
            return 1

        print(
            "Email outbox run completed: "
            f"recovered={result.recovered} "
            f"claimed={result.claimed} "
            f"sent={result.sent} "
            f"delivery_failures={result.delivery_failures}"
        )
        return 0

    parser.error("Unsupported command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
