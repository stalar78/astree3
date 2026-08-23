#!/bin/sh
set -eu
umask 077

fail() {
    printf '%s\n' "$*" >&2
    exit 1
}

require_root() {
    [ "$(id -u)" -eq 0 ] || fail "Root privileges are required."
}

validate_backup_root() {
    value=$1

    case "$value" in
        /*) ;;
        *) fail "ASTREA_BACKUP_ROOT must be an absolute path." ;;
    esac

    case "$value" in
        ''|*..*|*//*)
            fail "ASTREA_BACKUP_ROOT is not allowed."
            ;;
    esac

    case "$value" in
        /|/etc|/var|/var/backups|/home|/root|/etc/|/var/|/var/backups/|/home/|/root/)
            fail "ASTREA_BACKUP_ROOT is not allowed."
            ;;
    esac
}

: "${ASTREA_BACKUP_ROOT:=/var/backups/astrea}"

require_root
validate_backup_root "$ASTREA_BACKUP_ROOT"

if [ -L "$ASTREA_BACKUP_ROOT" ]; then
    fail "ASTREA_BACKUP_ROOT is not allowed."
fi

mkdir -p "$ASTREA_BACKUP_ROOT"
if [ -L "$ASTREA_BACKUP_ROOT" ]; then
    fail "ASTREA_BACKUP_ROOT is not allowed."
fi
chown 10001:10001 "$ASTREA_BACKUP_ROOT"
chmod 0700 "$ASTREA_BACKUP_ROOT"

printf '%s\n' "$ASTREA_BACKUP_ROOT"
