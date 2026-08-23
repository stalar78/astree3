#!/bin/sh
set -eu
umask 077

. /usr/local/bin/common.sh

: "${ASTREA_BACKUP_ROOT:=/backups}"
: "${PRIVATE_MEDIA_ROOT:=/var/lib/astrea/private}"
: "${ASTREA_BACKUP_QUIESCED:=}"
: "${PGHOST:=db}"
: "${PGPORT:=5432}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

ensure_confirmation "$ASTREA_BACKUP_QUIESCED" "BACKEND_WRITES_QUIESCED" "Backup requires quiescence acknowledgement."

backup_id=${ASTREA_BACKUP_ID:-$(generate_backup_id)}
validate_backup_id "$backup_id"

mkdir -p "$ASTREA_BACKUP_ROOT"

final_dir="$ASTREA_BACKUP_ROOT/$backup_id"
[ -e "$final_dir" ] && fail "Backup ID already exists."

tmp_dir=$(mktemp -d "$ASTREA_BACKUP_ROOT/.incomplete.${backup_id}.XXXXXX")
done=0

cleanup() {
    if [ "$done" -eq 0 ] && [ -n "${tmp_dir:-}" ] && [ -d "$tmp_dir" ]; then
        rm -rf "$tmp_dir"
    fi
}

trap cleanup EXIT HUP INT TERM

dump_path="$tmp_dir/database.dump"
archive_path="$tmp_dir/private-media.tar.gz"
checksums_path="$tmp_dir/checksums.sha256"
metadata_path="$tmp_dir/metadata.txt"

PGPASSWORD="$POSTGRES_PASSWORD" \
pg_dump \
    -h "$PGHOST" \
    -p "$PGPORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --format=custom \
    --no-owner \
    --no-acl \
    -f "$dump_path"

[ -s "$dump_path" ] || fail "Database dump is empty."

tar -C "$PRIVATE_MEDIA_ROOT" -czf "$archive_path" .
[ -s "$archive_path" ] || fail "Private media archive is empty."

alembic_version=$(alembic_revision)

{
    printf 'format_version=1\n'
    printf 'backup_id=%s\n' "$backup_id"
    printf 'created_at_utc=%s\n' "$(current_utc)"
    printf 'postgres_major_version=%s\n' "$(postgres_major_version)"
    printf 'database_name=%s\n' "$POSTGRES_DB"
    if [ -n "$alembic_version" ]; then
        printf 'alembic_revision=%s\n' "$alembic_version"
    fi
} > "$metadata_path"

(
    cd "$tmp_dir"
    sha256sum database.dump private-media.tar.gz > checksums.sha256
)

mv "$tmp_dir" "$final_dir"
done=1
trap - EXIT HUP INT TERM

printf '%s\n' "$final_dir"
