from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.admin_bootstrap import AdminBootstrapError, bootstrap_initial_admin


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="astrea-backend")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("bootstrap-admin", help="Create the initial admin user if needed.")
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

    parser.error("Unsupported command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
