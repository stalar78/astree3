#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/infra/.env.codespaces.local"
COMPOSE_FILE="${ROOT_DIR}/infra/compose.yml"
PROJECT_NAME="astrea-demo"
DEMO_PORT="18080"

fail() {
  printf 'Astrea demo: %s\n' "$*" >&2
  exit 1
}

compose() {
  docker compose \
    --project-name "${PROJECT_NAME}" \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    "$@"
}

random_uuid_compact() {
  tr -d '-' < /proc/sys/kernel/random/uuid
}

ensure_env() {
  if [[ -f "${ENV_FILE}" ]]; then
    return
  fi

  local postgres_password admin_password
  postgres_password="$(random_uuid_compact)$(random_uuid_compact)"
  admin_password="Demo-$(random_uuid_compact)"

  umask 077
  cat > "${ENV_FILE}" <<EOF
ASTREA_HTTP_PORT=${DEMO_PORT}
ASTREA_EDGE_SUBNET=172.30.250.0/24
ASTREA_PROXY_IP=172.30.250.10
POSTGRES_DB=astrea_demo
POSTGRES_USER=astrea_demo
POSTGRES_PASSWORD=${postgres_password}
APP_ENV=demo
ADMIN_LOGIN_RATE_LIMIT_REQUESTS=10
ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS=900
CANDIDATE_RATE_LIMIT_REQUESTS=5
CANDIDATE_RATE_LIMIT_WINDOW_SECONDS=900
VITE_CANDIDATE_FORM_ENABLED=false
VITE_PUBLIC_SITE_ORIGIN=
CANDIDATE_INTAKE_ENABLED=false
CANDIDATE_PERSONAL_DATA_CONSENT_VERSION=
CANDIDATE_PRIVACY_POLICY_VERSION=
CANDIDATE_SAINT_PETERSBURG_ACKNOWLEDGEMENT_VERSION=
DEMO_ADMIN_USERNAME=demo_admin
DEMO_ADMIN_PASSWORD=${admin_password}
EOF
  chmod 600 "${ENV_FILE}"
  printf 'Astrea demo: generated disposable credentials in %s\n' "${ENV_FILE}"
}

load_env() {
  ensure_env
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
}

wait_for_web() {
  local attempt
  for attempt in {1..90}; do
    if curl --fail --silent --show-error "http://127.0.0.1:${DEMO_PORT}/healthz" >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done

  compose ps >&2 || true
  fail "web did not become healthy on port ${DEMO_PORT}"
}

bootstrap_admin() {
  compose exec -T \
    -e "ADMIN_INITIAL_USERNAME=${DEMO_ADMIN_USERNAME}" \
    -e "ADMIN_INITIAL_PASSWORD=${DEMO_ADMIN_PASSWORD}" \
    backend python -m app.cli bootstrap-admin
}

start_demo() {
  load_env
  command -v docker >/dev/null 2>&1 || fail "Docker is not available in this environment"
  command -v curl >/dev/null 2>&1 || fail "curl is not available in this environment"

  printf 'Astrea demo: starting isolated Compose project %s...\n' "${PROJECT_NAME}"
  compose up -d --build
  wait_for_web
  bootstrap_admin

  printf '\nAstrea demo is ready.\n'
  printf 'Local endpoint: http://127.0.0.1:%s\n' "${DEMO_PORT}"
  printf 'The Codespaces forwarded port remains private until you run:\n'
  printf '  bash .devcontainer/demo.sh share\n'
}

require_codespaces() {
  [[ "${CODESPACES:-}" == "true" ]] || fail "this command must be run inside GitHub Codespaces"
  [[ -n "${CODESPACE_NAME:-}" ]] || fail "CODESPACE_NAME is not available"
  command -v gh >/dev/null 2>&1 || fail "GitHub CLI is not available"
}

demo_url() {
  local domain="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
  printf 'https://%s-%s.%s' "${CODESPACE_NAME}" "${DEMO_PORT}" "${domain}"
}

show_credentials() {
  load_env
  printf 'Demo admin URL: %s/admin/login\n' "$(demo_url)"
  printf 'Demo admin username: %s\n' "${DEMO_ADMIN_USERNAME}"
  printf 'Demo admin password: %s\n' "${DEMO_ADMIN_PASSWORD}"
}

share_demo() {
  require_codespaces
  load_env
  wait_for_web

  gh codespace ports visibility "${DEMO_PORT}:public" -c "${CODESPACE_NAME}"

  printf '\nAstrea client demo is PUBLIC. Anyone with this URL can open the site:\n'
  printf '%s\n\n' "$(demo_url)"
  show_credentials
  printf '\nWhen the client session is finished, close public access with:\n'
  printf '  bash .devcontainer/demo.sh private\n'
}

make_private() {
  require_codespaces
  gh codespace ports visibility "${DEMO_PORT}:private" -c "${CODESPACE_NAME}"
  printf 'Astrea demo port %s is private again.\n' "${DEMO_PORT}"
}

show_status() {
  load_env
  compose ps
  if curl --fail --silent "http://127.0.0.1:${DEMO_PORT}/healthz" >/dev/null 2>&1; then
    printf 'Astrea demo health: OK\n'
  else
    printf 'Astrea demo health: NOT READY\n' >&2
    return 1
  fi
}

usage() {
  cat <<'EOF'
Usage: bash .devcontainer/demo.sh <command>

Commands:
  bootstrap     Create disposable credentials, build/start the demo, bootstrap demo_admin.
  up            Build/start the demo and ensure demo_admin exists.
  share         Make forwarded port 18080 public and print the client URL and demo-admin login.
  private       Return forwarded port 18080 to private visibility.
  credentials   Print only the disposable demo-admin credentials.
  status        Show Compose state and demo health.
EOF
}

command_name="${1:-}"
case "${command_name}" in
  bootstrap|up)
    start_demo
    ;;
  share)
    share_demo
    ;;
  private)
    make_private
    ;;
  credentials)
    require_codespaces
    show_credentials
    ;;
  status)
    show_status
    ;;
  *)
    usage
    [[ -n "${command_name}" ]] || exit 0
    exit 2
    ;;
esac
