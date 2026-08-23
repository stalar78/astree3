#!/bin/sh
set -eu

LOCK_FILE=${ASTREA_OPS_LOCK_FILE:-/run/lock/astrea-ops.lock}
LOCK_WAIT_SECONDS=${ASTREA_OPS_LOCK_WAIT_SECONDS:-300}
BACKEND_STOP_TIMEOUT_SECONDS=${ASTREA_BACKEND_STOP_TIMEOUT_SECONDS:-30}
BACKEND_HEALTH_TIMEOUT_SECONDS=${ASTREA_BACKEND_HEALTH_TIMEOUT_SECONDS:-300}
backend_should_restart=0
backend_restart_failed=0
backend_cleanup_attempted=0
signal_received=0

fail() {
    printf '%s\n' "$*" >&2
    exit 1
}

require_value() {
    name=$1
    value=$2

    [ -n "$value" ] || fail "$name is required."
}

require_absolute_path() {
    name=$1
    value=$2

    case "$value" in
        /*) ;;
        *) fail "$name must be an absolute path." ;;
    esac
}

validate_project_name() {
    value=$1

    case "$value" in
        ''|*[!A-Za-z0-9._-]*)
            fail "ASTREA_COMPOSE_PROJECT_NAME is invalid."
            ;;
    esac
}

compose() {
    docker compose \
        --profile ops \
        --env-file "$ASTREA_ENV_FILE" \
        -f "$ASTREA_PROJECT_DIR/infra/compose.yml" \
        -p "$ASTREA_COMPOSE_PROJECT_NAME" \
        "$@"
}

service_container_id() {
    service=$1
    compose ps -q "$service" 2>/dev/null || true
}

service_is_running() {
    service=$1
    container_id=$(service_container_id "$service")
    [ -n "$container_id" ] || return 1
    [ "$(docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null || printf false)" = true ]
}

service_health_status() {
    service=$1
    container_id=$(service_container_id "$service")
    [ -n "$container_id" ] || return 1
    docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null
}

wait_for_service_state() {
    service=$1
    expected=$2
    deadline=$(( $(date +%s) + $3 ))

    while :; do
        current=$(service_health_status "$service" 2>/dev/null || printf absent)
        case "$current" in
            "$expected")
                return 0
                ;;
        esac
        if [ "$(date +%s)" -ge "$deadline" ]; then
            return 1
        fi
        sleep 2
    done
}

wait_for_backend_stopped() {
    deadline=$(( $(date +%s) + BACKEND_STOP_TIMEOUT_SECONDS ))

    while :; do
        if ! service_is_running backend; then
            return 0
        fi
        if [ "$(date +%s)" -ge "$deadline" ]; then
            return 1
        fi
        sleep 2
    done
}

wait_for_backend_healthy() {
    deadline=$(( $(date +%s) + BACKEND_HEALTH_TIMEOUT_SECONDS ))

    while :; do
        health_status=$(service_health_status backend 2>/dev/null || printf absent)
        case "$health_status" in
            healthy)
                return 0
                ;;
        esac
        if [ "$(date +%s)" -ge "$deadline" ]; then
            return 1
        fi
        sleep 2
    done
}

acquire_lock() {
    mkdir -p "$(dirname "$LOCK_FILE")"
    exec 9>"$LOCK_FILE"
    if ! flock -w "$LOCK_WAIT_SECONDS" 9; then
        fail "astrea-ops: lock unavailable."
    fi
}

cleanup_backend() {
    if [ "$backend_should_restart" -eq 1 ] && [ "$backend_cleanup_attempted" -eq 0 ]; then
        backend_cleanup_attempted=1
        if ! compose up -d backend; then
            backend_restart_failed=1
            return 1
        fi
        if ! wait_for_backend_healthy; then
            backend_restart_failed=1
            return 1
        fi
        backend_should_restart=0
    fi
}

on_signal() {
    signal_received=1
    exit 130
}

on_exit() {
    exit_code=$?
    trap - EXIT HUP INT TERM
    if [ "$backend_should_restart" -eq 1 ]; then
        cleanup_backend || :
    fi
    if [ "$backend_restart_failed" -ne 0 ] && [ "$exit_code" -eq 0 ]; then
        exit_code=1
    fi
    exit "$exit_code"
}

run_backup() {
    backend_was_running=0
    if service_is_running backend; then
        backend_was_running=1
        backend_should_restart=1
    fi

    if [ "$backend_was_running" -eq 1 ]; then
        printf 'astrea-ops backup: stopping backend\n'
        if ! compose stop -t "$BACKEND_STOP_TIMEOUT_SECONDS" backend; then
            fail "astrea-ops backup: failed to stop backend."
        fi
        if ! wait_for_backend_stopped; then
            fail "astrea-ops backup: backend did not stop cleanly."
        fi
    fi

    backup_status=0
    set +e
    compose run --rm -e ASTREA_BACKUP_QUIESCED=BACKEND_WRITES_QUIESCED backup
    backup_status=$?
    set -e

    if [ "$backup_status" -ne 0 ]; then
        return "$backup_status"
    fi
}

run_email_worker() {
    set +e
    compose run --rm email-worker
    status=$?
    set -e
    return "$status"
}

run_smtp_check() {
    set +e
    compose run --rm smtp-check
    status=$?
    set -e
    return "$status"
}

run_prune() {
    set +e
    compose run --rm \
        -e ASTREA_PRUNE_CONFIRM=PRUNE_AUTOMATIC_BACKUPS \
        -e ASTREA_PRUNE_DRY_RUN=false \
        -e ASTREA_BACKUP_RETENTION_COUNT="$ASTREA_BACKUP_RETENTION_COUNT" \
        prune
    status=$?
    set -e
    return "$status"
}

[ $# -eq 1 ] || fail "Usage: astrea-ops.sh {backup|email-worker|smtp-check|prune}"

command=$1

require_value ASTREA_PROJECT_DIR "${ASTREA_PROJECT_DIR:-}"
require_value ASTREA_ENV_FILE "${ASTREA_ENV_FILE:-}"
require_value ASTREA_BACKUP_ROOT "${ASTREA_BACKUP_ROOT:-}"
require_value ASTREA_BACKUP_RETENTION_COUNT "${ASTREA_BACKUP_RETENTION_COUNT:-}"
require_absolute_path ASTREA_PROJECT_DIR "$ASTREA_PROJECT_DIR"
require_absolute_path ASTREA_ENV_FILE "$ASTREA_ENV_FILE"
require_absolute_path ASTREA_BACKUP_ROOT "$ASTREA_BACKUP_ROOT"
case "$ASTREA_BACKUP_RETENTION_COUNT" in
    ''|*[!0-9]*)
        fail "ASTREA_BACKUP_RETENTION_COUNT must be numeric."
        ;;
esac
validate_project_name "${ASTREA_COMPOSE_PROJECT_NAME:=astrea}"

trap on_exit EXIT
trap on_signal HUP INT TERM

case "$command" in
    backup|email-worker|smtp-check|prune)
        ;;
    *)
        fail "Unsupported command."
        ;;
esac

acquire_lock

status=0
case "$command" in
    backup)
        printf 'astrea-ops backup: started\n'
        if run_backup; then
            :
        else
            status=$?
        fi
        ;;
    email-worker)
        printf 'astrea-ops email-worker: started\n'
        if run_email_worker; then
            :
        else
            status=$?
        fi
        ;;
    smtp-check)
        printf 'astrea-ops smtp-check: started\n'
        if run_smtp_check; then
            :
        else
            status=$?
        fi
        ;;
    prune)
        printf 'astrea-ops prune: started\n'
        if run_prune; then
            :
        else
            status=$?
        fi
        ;;
esac

if [ "$command" = backup ] && [ "$backend_should_restart" -eq 1 ]; then
    printf 'astrea-ops backup: restarting backend\n'
    if ! cleanup_backend; then
        backend_restart_failed=1
    fi
fi

if [ "$status" -eq 0 ] && [ "$backend_restart_failed" -eq 0 ]; then
    case "$command" in
        backup)
            printf 'astrea-ops backup: completed\n'
            ;;
        email-worker)
            printf 'astrea-ops email-worker: completed\n'
            ;;
        smtp-check)
            printf 'astrea-ops smtp-check: completed\n'
            ;;
        prune)
            printf 'astrea-ops prune: completed\n'
            ;;
    esac
else
    case "$command" in
        backup)
            printf 'astrea-ops backup: failed\n' >&2
            ;;
        email-worker)
            printf 'astrea-ops email-worker: failed\n' >&2
            ;;
        smtp-check)
            printf 'astrea-ops smtp-check: failed\n' >&2
            ;;
        prune)
            printf 'astrea-ops prune: failed\n' >&2
            ;;
    esac
fi

if [ "$status" -ne 0 ]; then
    exit "$status"
fi

if [ "$backend_restart_failed" -ne 0 ]; then
    exit 1
fi
