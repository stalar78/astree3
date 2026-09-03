#!/bin/sh
set -eu

fail() {
    printf 'production-smoke: FAIL: %s\n' "$*" >&2
    exit 1
}

pass() {
    printf 'production-smoke: PASS: %s\n' "$*"
}

[ $# -eq 1 ] || fail "usage: production-smoke.sh https://production-origin"

ORIGIN=${1%/}
case "$ORIGIN" in
    https://*/*|https://*\?*|https://*\#*)
        fail "origin must be one bare HTTPS origin"
        ;;
    https://*) ;;
    *) fail "origin must use HTTPS" ;;
esac

command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v grep >/dev/null 2>&1 || fail "grep is required"
command -v mktemp >/dev/null 2>&1 || fail "mktemp is required"

TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT HUP INT TERM

HEADERS="$TMP_ROOT/headers"
BODY="$TMP_ROOT/body"

request() {
    method=$1
    path=$2
    : >"$HEADERS"
    : >"$BODY"
    curl \
        --silent \
        --show-error \
        --location \
        --max-redirs 3 \
        --connect-timeout 10 \
        --max-time 30 \
        --request "$method" \
        --dump-header "$HEADERS" \
        --output "$BODY" \
        --write-out '%{http_code}' \
        "$ORIGIN$path"
}

expect_status() {
    method=$1
    path=$2
    expected=$3
    status=$(request "$method" "$path") || fail "$method $path request failed"
    [ "$status" = "$expected" ] || fail "$method $path returned $status, expected $expected"
}

expect_header() {
    name=$1
    pattern=$2
    grep -Eiq "^${name}:[[:space:]]*${pattern}" "$HEADERS" || fail "missing or invalid $name header"
}

expect_status GET / 200
expect_header Strict-Transport-Security '.*max-age=' 
expect_header Content-Security-Policy '.+'
expect_header Permissions-Policy '.+'
expect_header Referrer-Policy 'strict-origin-when-cross-origin'
expect_header X-Content-Type-Options 'nosniff'
expect_header X-Frame-Options 'SAMEORIGIN'
pass "public root and HTTPS security headers"

expect_status GET /healthz 200
expect_header X-Robots-Tag '.*noindex.*nofollow.*noarchive'
grep -q '^ok' "$BODY" || fail "/healthz body is unexpected"
pass "web health endpoint"

expect_status GET /api/v1/health 200
expect_header X-Robots-Tag '.*noindex.*nofollow.*noarchive'
grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' "$BODY" || fail "API health body is unexpected"
pass "backend health endpoint"

expect_status GET /admin/login 200
expect_header X-Robots-Tag '.*noindex.*nofollow.*noarchive'
pass "admin login shell remains noindex"

expect_status GET /api/v1/admin/auth/me 401
expect_header X-Robots-Tag '.*noindex.*nofollow.*noarchive'
pass "admin API rejects unauthenticated access"

expect_status GET /api/v1/admin/candidates/1/photo 401
pass "private candidate photo endpoint rejects unauthenticated access"

expect_status POST /api/v1/candidate-applications 404
pass "candidate intake remains disabled"

expect_status GET /robots.txt 200
grep -Fq 'Disallow: /admin' "$BODY" || fail "robots.txt does not disallow /admin"
grep -Fq 'Disallow: /api/' "$BODY" || fail "robots.txt does not disallow /api/"
grep -Fq 'Disallow: /healthz' "$BODY" || fail "robots.txt does not disallow /healthz"
pass "robots controls"

for path in /o-lozhe /novosti /video /faq /kontakty /vstuplenie; do
    expect_status GET "$path" 200
    pass "public route $path"
done

printf 'production-smoke: ALL CHECKS PASSED for %s\n' "$ORIGIN"
