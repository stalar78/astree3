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
