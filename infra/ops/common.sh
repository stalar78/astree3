#!/bin/sh

fail() {
    printf '%s\n' "$*" >&2
    exit 1
}

validate_backup_id() {
    backup_id=$1

    case "$backup_id" in
        ''|.*|*..*|*/*|*\\*|*[[:space:]]*|*[!A-Za-z0-9._-]*)
            fail "Invalid backup ID."
            ;;
    esac
}

generate_backup_id() {
    timestamp=$(date -u +%Y%m%dT%H%M%SZ)
    suffix=$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')
    printf '%s-%s' "$timestamp" "$suffix"
}

ensure_confirmation() {
    value=$1
    expected=$2
    message=$3

    if [ "$value" != "$expected" ]; then
        fail "$message"
    fi
}

current_utc() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

postgres_major_version() {
    server_version_num=$(
        PGPASSWORD="$POSTGRES_PASSWORD" \
        psql -h "$PGHOST" -p "$PGPORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc 'show server_version_num'
    )
    printf '%s\n' "$((server_version_num / 10000))"
}

alembic_revision() {
    PGPASSWORD="$POSTGRES_PASSWORD" \
    psql -h "$PGHOST" -p "$PGPORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc 'select version_num from alembic_version limit 1' 2>/dev/null || true
}

validate_retention_count() {
    retention_count=$1

    case "$retention_count" in
        ''|*[!0-9]*)
            fail "Invalid retention count."
            ;;
    esac

    if [ "$retention_count" -lt 7 ] || [ "$retention_count" -gt 365 ]; then
        fail "Invalid retention count."
    fi
}

is_automatic_backup_id() {
    backup_id=$1

    case "$backup_id" in
        [0-9][0-9][0-9][0-9][0-1][0-9][0-3][0-9]T[0-2][0-9][0-5][0-9][0-5][0-9]Z-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f])
            return 0
            ;;
    esac

    return 1
}

validate_true_false_flag() {
    value=$1

    case "$value" in
        true|false)
            return 0
            ;;
    esac

    fail "Invalid boolean flag."
}
