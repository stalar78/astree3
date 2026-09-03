#!/bin/sh
set -eu

fail() {
    printf 'production-preflight: FAIL: %s\n' "$*" >&2
    exit 1
}

pass() {
    printf 'production-preflight: PASS: %s\n' "$*"
}

[ $# -eq 2 ] || fail "usage: production-preflight.sh PROJECT_DIR ENV_FILE"

PROJECT_DIR=$1
ENV_FILE=$2

[ -d "$PROJECT_DIR" ] || fail "project directory does not exist"
[ -f "$ENV_FILE" ] || fail "production environment file does not exist"
[ ! -L "$ENV_FILE" ] || fail "production environment file must not be a symlink"

command -v docker >/dev/null 2>&1 || fail "docker is not installed"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 is not available"

read_env_value() {
    key=$1
    line=$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)
    [ -n "$line" ] || return 1
    printf '%s' "${line#*=}"
}

require_value() {
    key=$1
    value=$(read_env_value "$key" || true)
    [ -n "$value" ] || fail "$key is missing or empty"
}

require_exact() {
    key=$1
    expected=$2
    value=$(read_env_value "$key" || true)
    [ "$value" = "$expected" ] || fail "$key must equal $expected"
}

require_value APP_ENV
require_exact APP_ENV production
require_value POSTGRES_PASSWORD
require_value VITE_PUBLIC_SITE_ORIGIN
require_value ASTREA_EDGE_SUBNET
require_value ASTREA_HOST_PROXY_IP
require_value ASTREA_PROXY_IP
require_value ASTREA_BACKUP_ROOT
require_exact VITE_CANDIDATE_FORM_ENABLED false
require_exact CANDIDATE_INTAKE_ENABLED false

origin=$(read_env_value VITE_PUBLIC_SITE_ORIGIN)
case "$origin" in
    https://*/*|https://*\?*|https://*\#*|https://*/)
        fail "VITE_PUBLIC_SITE_ORIGIN must be one bare HTTPS origin without path, query, fragment or trailing slash"
        ;;
    https://*) ;;
    *) fail "VITE_PUBLIC_SITE_ORIGIN must use HTTPS" ;;
esac

case "$origin" in
    *replace-me*|*.invalid*) fail "VITE_PUBLIC_SITE_ORIGIN still contains a template placeholder" ;;
esac

password=$(read_env_value POSTGRES_PASSWORD)
case "$password" in
    replace-*|replace-me*|changeme|password|astrea)
        fail "POSTGRES_PASSWORD still uses a placeholder or weak template value"
        ;;
esac
[ "${#password}" -ge 20 ] || fail "POSTGRES_PASSWORD must be at least 20 characters"
unset password

if grep -Eq '=(replace-with-|replace-me|changeme)' "$ENV_FILE"; then
    fail "production environment file still contains replacement placeholders"
fi

if command -v stat >/dev/null 2>&1; then
    mode=$(stat -c '%a' "$ENV_FILE" 2>/dev/null || true)
    owner=$(stat -c '%u' "$ENV_FILE" 2>/dev/null || true)
    if [ -n "$mode" ] && [ "$mode" != "600" ]; then
        fail "production environment file mode must be 600"
    fi
    if [ -n "$owner" ] && [ "$owner" != "0" ]; then
        fail "production environment file must be root-owned"
    fi
fi

cd "$PROJECT_DIR"

docker compose \
    --env-file "$ENV_FILE" \
    -f infra/compose.yml \
    -p astrea \
    config -q || fail "normal Compose configuration is invalid"

docker compose \
    --profile ops \
    --env-file "$ENV_FILE" \
    -f infra/compose.yml \
    -p astrea \
    config -q || fail "ops Compose configuration is invalid"

pass "environment contract and Compose configuration"
