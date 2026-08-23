#!/bin/sh
set -eu
umask 077

. /usr/local/bin/common.sh

validate_checksums_manifest() {
    manifest=$1

    manifest_values=$(
        awk '
            function fail() {
                print "Invalid checksum manifest." > "/dev/stderr"
                exit 1
            }

            {
                sub(/\r$/, "")
                if ($0 == "") {
                    next
                }
                if (NF != 2) {
                    fail()
                }
                hash = $1
                path = $2
                if (length(hash) != 64 || hash !~ /^[0-9a-f]+$/) {
                    fail()
                }
                if (path == "database.dump") {
                    if (db_seen++) {
                        fail()
                    }
                    db_hash = hash
                } else if (path == "private-media.tar.gz") {
                    if (media_seen++) {
                        fail()
                    }
                    media_hash = hash
                } else {
                    fail()
                }
            }

            END {
                if (!db_seen || !media_seen) {
                    fail()
                }
                printf "%s|%s\n", db_hash, media_hash
            }
        ' "$manifest"
    ) || fail "Invalid checksum manifest."

    IFS='|' read -r db_expected media_expected <<EOF
$manifest_values
EOF
}

validate_metadata() {
    metadata=$1
    seen_format=0
    seen_backup=0
    seen_created=0
    seen_postgres=0
    seen_database=0

    while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] || fail "Invalid metadata."
        case "$line" in
            *=*)
                key=${line%%=*}
                value=${line#*=}
                ;;
            *)
                fail "Invalid metadata."
                ;;
        esac

        case "$key" in
            format_version)
                [ "$seen_format" -eq 0 ] || fail "Invalid metadata."
                [ "$value" = "1" ] || fail "Invalid metadata."
                seen_format=1
                ;;
            backup_id)
                [ "$seen_backup" -eq 0 ] || fail "Invalid metadata."
                [ -n "$value" ] || fail "Invalid metadata."
                [ "$value" = "$ASTREA_BACKUP_ID" ] || fail "Invalid metadata."
                seen_backup=1
                ;;
            created_at_utc)
                [ "$seen_created" -eq 0 ] || fail "Invalid metadata."
                [ -n "$value" ] || fail "Invalid metadata."
                seen_created=1
                ;;
            postgres_major_version)
                [ "$seen_postgres" -eq 0 ] || fail "Invalid metadata."
                case "$value" in
                    ''|*[!0-9]*)
                        fail "Invalid metadata."
                        ;;
                esac
                seen_postgres=1
                ;;
            database_name)
                [ "$seen_database" -eq 0 ] || fail "Invalid metadata."
                [ "$value" = "$POSTGRES_DB" ] || fail "Invalid metadata."
                seen_database=1
                ;;
            alembic_revision)
                [ -n "$value" ] || fail "Invalid metadata."
                ;;
            *)
                fail "Invalid metadata."
                ;;
        esac
    done < "$metadata"

    [ "$seen_format" -eq 1 ] || fail "Invalid metadata."
    [ "$seen_backup" -eq 1 ] || fail "Invalid metadata."
    [ "$seen_created" -eq 1 ] || fail "Invalid metadata."
    [ "$seen_postgres" -eq 1 ] || fail "Invalid metadata."
    [ "$seen_database" -eq 1 ] || fail "Invalid metadata."
}

validate_archive_entries() (
    archive=$1
    list_file=$(mktemp)
    verbose_file=$(mktemp)
    trap 'rm -f "$list_file" "$verbose_file"' EXIT HUP INT TERM

    tar -tzf "$archive" > "$list_file"
    tar -tvzf "$archive" > "$verbose_file"

    while IFS= read -r entry || [ -n "$entry" ]; do
        case "$entry" in
            ''|./|./.)
                continue
                ;;
            /*|*..*|*\\*|*:*|*[[:space:]]*)
                fail "Unsafe archive entry detected."
                ;;
        esac
    done < "$list_file"

    while IFS= read -r line || [ -n "$line" ]; do
        [ -n "$line" ] || continue
        case "$line" in
            d*)
                :
                ;;
            -*)
                case "$line" in
                    *" -> "*) fail "Unsafe archive entry detected." ;;
                esac
                ;;
            *)
                fail "Unsafe archive entry detected."
                ;;
        esac
    done < "$verbose_file"

    rm -f "$list_file" "$verbose_file"
)

validate_stage_tree() {
    stage_dir=$1

    if [ -n "$(find "$stage_dir" ! -type d ! -type f -print -quit)" ]; then
        fail "Unsafe archive entry detected."
    fi
}

: "${ASTREA_BACKUP_ROOT:=/backups}"
: "${PRIVATE_MEDIA_ROOT:=/var/lib/astrea/private}"
: "${ASTREA_RESTORE_CONFIRM:=}"
: "${ASTREA_RESTORE_QUIESCED:=}"
: "${ASTREA_BACKUP_ID:=}"
: "${PGHOST:=db}"
: "${PGPORT:=5432}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

ensure_confirmation "$ASTREA_RESTORE_CONFIRM" "RESTORE_ASTREA_DATA" "Restore requires explicit destructive confirmation."
ensure_confirmation "$ASTREA_RESTORE_QUIESCED" "BACKEND_STOPPED" "Restore requires backend stopped acknowledgement."

[ -n "$ASTREA_BACKUP_ID" ] || fail "ASTREA_BACKUP_ID is required."
validate_backup_id "$ASTREA_BACKUP_ID"

backup_dir="$ASTREA_BACKUP_ROOT/$ASTREA_BACKUP_ID"
[ -d "$backup_dir" ] || fail "Backup set not found."

dump_path="$backup_dir/database.dump"
archive_path="$backup_dir/private-media.tar.gz"
checksums_path="$backup_dir/checksums.sha256"
metadata_path="$backup_dir/metadata.txt"

[ -f "$dump_path" ] || fail "Missing database dump."
[ -f "$archive_path" ] || fail "Missing private media archive."
[ -f "$checksums_path" ] || fail "Missing checksum manifest."
[ -f "$metadata_path" ] || fail "Missing metadata."

validate_checksums_manifest "$checksums_path"

actual_dump_hash=$(sha256sum "$dump_path" | awk '{print $1}')
actual_archive_hash=$(sha256sum "$archive_path" | awk '{print $1}')

[ "$actual_dump_hash" = "$db_expected" ] || fail "Checksum mismatch."
[ "$actual_archive_hash" = "$media_expected" ] || fail "Checksum mismatch."

validate_metadata "$metadata_path"

PGPASSWORD="$POSTGRES_PASSWORD" \
pg_restore --list "$dump_path" >/dev/null

validate_archive_entries "$archive_path"

mkdir -p "$PRIVATE_MEDIA_ROOT"
stage_dir=$(mktemp -d "$PRIVATE_MEDIA_ROOT/.restore-stage.XXXXXX")
done=0

cleanup() {
    if [ "$done" -eq 0 ] && [ -n "${stage_dir:-}" ] && [ -d "$stage_dir" ]; then
        rm -rf "$stage_dir"
    fi
}

trap cleanup EXIT HUP INT TERM

tar -xzf "$archive_path" -C "$stage_dir"
validate_stage_tree "$stage_dir"

PGPASSWORD="$POSTGRES_PASSWORD" \
pg_restore \
    -h "$PGHOST" \
    -p "$PGPORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --single-transaction \
    --exit-on-error \
    "$dump_path"

stage_name=$(basename "$stage_dir")
find "$PRIVATE_MEDIA_ROOT" -mindepth 1 -maxdepth 1 ! -name "$stage_name" -exec rm -rf {} +
cp -a "$stage_dir"/. "$PRIVATE_MEDIA_ROOT"/
rm -rf "$stage_dir"

done=1
trap - EXIT HUP INT TERM

printf '%s\n' "$backup_dir"
