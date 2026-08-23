#!/bin/sh
set -eu
umask 077

. /usr/local/bin/common.sh

validate_prune_metadata() {
    metadata=$1
    expected_backup_id=$2

    format_seen=0
    backup_seen=0
    origin_seen=0
    backup_origin=
    created_seen=0
    postgres_seen=0
    database_seen=0
    alembic_seen=0

    while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] || return 1
        case "$line" in
            *=*)
                key=${line%%=*}
                value=${line#*=}
                ;;
            *)
                return 1
                ;;
        esac

        case "$key" in
            format_version)
                [ "$format_seen" -eq 0 ] || return 1
                [ "$value" = "1" ] || return 1
                format_seen=1
                ;;
            backup_id)
                [ "$backup_seen" -eq 0 ] || return 1
                [ "$value" = "$expected_backup_id" ] || return 1
                backup_seen=1
                ;;
            backup_origin)
                [ "$origin_seen" -eq 0 ] || return 1
                case "$value" in
                    automatic|operator)
                        backup_origin=$value
                        ;;
                    *)
                        return 1
                        ;;
                esac
                origin_seen=1
                ;;
            created_at_utc)
                [ "$created_seen" -eq 0 ] || return 1
                [ -n "$value" ] || return 1
                created_seen=1
                ;;
            postgres_major_version)
                [ "$postgres_seen" -eq 0 ] || return 1
                case "$value" in
                    ''|*[!0-9]*)
                        return 1
                        ;;
                esac
                postgres_seen=1
                ;;
            database_name)
                [ "$database_seen" -eq 0 ] || return 1
                [ -n "$value" ] || return 1
                database_seen=1
                ;;
            alembic_revision)
                [ "$alembic_seen" -eq 0 ] || return 1
                [ -n "$value" ] || return 1
                alembic_seen=1
                ;;
            *)
                return 1
                ;;
        esac
    done < "$metadata"

    [ "$format_seen" -eq 1 ] || return 1
    [ "$backup_seen" -eq 1 ] || return 1
    [ "$created_seen" -eq 1 ] || return 1
    [ "$postgres_seen" -eq 1 ] || return 1
    [ "$database_seen" -eq 1 ] || return 1
    [ "$origin_seen" -eq 1 ] || return 1
    [ "$backup_origin" = automatic ] || return 1
}

validate_completed_backup_dir() {
    backup_dir=$1
    backup_id=$2

    [ -d "$backup_dir" ] || return 1
    [ ! -L "$backup_dir" ] || return 1
    is_automatic_backup_id "$backup_id" || return 1

    dump_path="$backup_dir/database.dump"
    archive_path="$backup_dir/private-media.tar.gz"
    checksums_path="$backup_dir/checksums.sha256"
    metadata_path="$backup_dir/metadata.txt"

    [ -f "$dump_path" ] || return 1
    [ -f "$archive_path" ] || return 1
    [ -f "$checksums_path" ] || return 1
    [ -f "$metadata_path" ] || return 1
    [ ! -L "$dump_path" ] || return 1
    [ ! -L "$archive_path" ] || return 1
    [ ! -L "$checksums_path" ] || return 1
    [ ! -L "$metadata_path" ] || return 1

    validate_prune_metadata "$metadata_path" "$backup_id"
}

delete_completed_backup_dir() {
    backup_dir=$1
    backup_id=$2

    validate_completed_backup_dir "$backup_dir" "$backup_id" || fail "Invalid backup set."
    rm -rf -- "$backup_dir"
}

eligible_ids_file=
sorted_ids_file=
delete_ids_file=

: "${ASTREA_BACKUP_ROOT:=/backups}"
: "${ASTREA_PRUNE_CONFIRM:=}"
: "${ASTREA_PRUNE_DRY_RUN:=true}"
: "${ASTREA_BACKUP_RETENTION_COUNT:=14}"

[ -d "$ASTREA_BACKUP_ROOT" ] || fail "Backup root not found."
validate_retention_count "$ASTREA_BACKUP_RETENTION_COUNT"
validate_true_false_flag "$ASTREA_PRUNE_DRY_RUN"

if [ "$ASTREA_PRUNE_DRY_RUN" = false ]; then
    ensure_confirmation "$ASTREA_PRUNE_CONFIRM" "PRUNE_AUTOMATIC_BACKUPS" "Prune requires explicit destructive confirmation."
fi

eligible_ids_file=$(mktemp)
trap 'rm -f "$eligible_ids_file"' EXIT HUP INT TERM

for backup_dir in "$ASTREA_BACKUP_ROOT"/*; do
    [ -e "$backup_dir" ] || continue
    [ -d "$backup_dir" ] || continue
    [ ! -L "$backup_dir" ] || continue

    backup_id=${backup_dir##*/}
    validate_completed_backup_dir "$backup_dir" "$backup_id" || continue
    printf '%s\n' "$backup_id" >> "$eligible_ids_file"
done

sorted_ids_file=$(mktemp)
trap 'rm -f "$eligible_ids_file" "$sorted_ids_file"' EXIT HUP INT TERM
sort "$eligible_ids_file" > "$sorted_ids_file"
mv "$sorted_ids_file" "$eligible_ids_file"
eligible_count=$(wc -l < "$eligible_ids_file" | tr -d ' ')
keep_count=$ASTREA_BACKUP_RETENTION_COUNT

if [ "$eligible_count" -le "$keep_count" ]; then
    printf 'prune: eligible=%s keep=%s delete=0\n' "$eligible_count" "$keep_count"
    exit 0
fi

delete_count=$((eligible_count - keep_count))
delete_ids_file=$(mktemp)
trap 'rm -f "$eligible_ids_file" "$delete_ids_file"' EXIT HUP INT TERM
head -n "$delete_count" "$eligible_ids_file" > "$delete_ids_file"

printf 'prune: eligible=%s keep=%s delete=%s\n' "$eligible_count" "$keep_count" "$delete_count"

if [ "$ASTREA_PRUNE_DRY_RUN" = true ]; then
    while IFS= read -r backup_id || [ -n "$backup_id" ]; do
        [ -n "$backup_id" ] || continue
        printf 'prune dry-run delete: %s\n' "$backup_id"
    done < "$delete_ids_file"
    exit 0
fi

while IFS= read -r backup_id || [ -n "$backup_id" ]; do
    [ -n "$backup_id" ] || continue
    backup_dir="$ASTREA_BACKUP_ROOT/$backup_id"
    printf 'prune delete: %s\n' "$backup_id"
    delete_completed_backup_dir "$backup_dir" "$backup_id"
done < "$delete_ids_file"

printf 'prune: completed deleted=%s\n' "$delete_count"
