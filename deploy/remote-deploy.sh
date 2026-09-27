#!/usr/bin/env bash
# Runs on the VPS. Installs one release bundle, starts it on Guess-Warrior's
# reserved port, and (when APP_URL is set) points the subdomain at it.
#
#   remote-deploy.sh <release-id> <path-to-release.tar.gz> [--dry-run]
#
# Layout under APP_DIR (default ~/guess-warrior):
#   releases/<id>/          one directory per deploy (last KEEP_RELEASES kept)
#   current -> releases/<id>
#   shared/.env             production settings, created on first deploy
#   shared/venvs/<hash>/    Python virtualenv per requirements.txt version, so
#                           torch is only downloaded when requirements change
#   shared/hf-cache/        sentence-transformers model, downloaded once
#
# Port: reserved once from PORT_RANGE in /etc/port-registry ("<app> <port>")
# and reused on every deploy. Other apps are never stopped or moved. The
# registry is shared with the other apps on the server (e.g. KleanLink).
#
# The app runs as the systemd service "guess-warrior" (gunicorn, one worker,
# because game rooms live in memory).
#
# If the new release fails its health check, the previous release is started
# again and the script exits non-zero; nginx is only switched after the new
# release is healthy. Without APP_URL, nginx is left alone and the app is only
# reachable on 127.0.0.1:<port>.
#
# --dry-run prints the port, nginx and certificate plan and changes nothing.

set -euo pipefail

RELEASE_ID="${1:?release id required}"
ARCHIVE="${2:?archive path required}"
DRY_RUN=false
[ "${3:-}" = "--dry-run" ] && DRY_RUN=true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

APP_NAME="${APP_NAME:-guess-warrior}"
APP_DIR="${APP_DIR:-$HOME/guess-warrior}"
APP_URL="${APP_URL:-}"
PORT_RANGE="${PORT_RANGE:-5100-5199}"
PORT_REGISTRY="${PORT_REGISTRY:-/etc/port-registry}"
MANAGE_NGINX="${MANAGE_NGINX:-true}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"
KEEP_VENVS="${KEEP_VENVS:-2}"

RELEASES="$APP_DIR/releases"
SHARED="$APP_DIR/shared"
RELEASE="$RELEASES/$RELEASE_ID"
SERVICE="$APP_NAME.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE"
DOMAIN="$(printf '%s' "$APP_URL" | sed -E 's#^[a-z]+://##; s#[/:].*$##')"

log() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  sudo -n true 2>/dev/null || fail "This deploy needs root or passwordless sudo (port registry, systemd, nginx)."
  SUDO="sudo -n"
fi

# ---------------------------------------------------------------- prerequisites
command -v python3 >/dev/null || fail "python3 is not installed on this server (need 3.9+)."
python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' \
  || fail "Python $(python3 -V) is too old; install 3.9 or newer."
python3 -c 'import venv, ensurepip' 2>/dev/null \
  || fail "python3-venv is missing. Run: sudo apt install python3-venv"
command -v systemctl >/dev/null || fail "systemd is required on the server."
command -v curl >/dev/null || fail "curl is required on the server."
command -v ss >/dev/null || fail "ss (iproute2) is required on the server."

# ---------------------------------------------------------- port reservation
port_in_use() {
  $SUDO ss -ltnH "sport = :$1" | grep -q .
}

# True when the listener on the port is our own service.
port_is_ours() {
  local main_pid pid
  main_pid="$(systemctl show -p MainPID --value "$SERVICE" 2>/dev/null || echo 0)"
  [ "${main_pid:-0}" != 0 ] || return 1
  for pid in $($SUDO ss -ltnpH "sport = :$1" | grep -o 'pid=[0-9]*' | cut -d= -f2); do
    # gunicorn's worker holds the socket too; accept the master or its children.
    [ "$pid" = "$main_pid" ] && return 0
    [ "$(ps -o ppid= -p "$pid" | tr -d ' ')" = "$main_pid" ] && return 0
  done
  return 1
}

# A dry run only reads the registry; it never creates or changes it.
if [ ! -f "$PORT_REGISTRY" ] && [ "$DRY_RUN" = false ]; then
  $SUDO touch "$PORT_REGISTRY"
fi
PORT=""
if [ -f "$PORT_REGISTRY" ]; then
  PORT="$(awk -v app="$APP_NAME" '$1 == app { print $2 }' "$PORT_REGISTRY" | tail -n 1)"
fi

if [ -n "$PORT" ]; then
  if port_in_use "$PORT" && ! port_is_ours "$PORT"; then
    fail "Port $PORT is reserved for $APP_NAME in $PORT_REGISTRY but another process is listening on it: $($SUDO ss -ltnpH "sport = :$PORT")"
  fi
  echo "Using reserved port $PORT"
else
  RANGE_START="${PORT_RANGE%-*}"
  RANGE_END="${PORT_RANGE#*-}"
  for candidate in $(seq "$RANGE_START" "$RANGE_END"); do
    if [ -f "$PORT_REGISTRY" ] && awk -v p="$candidate" '$2 == p { found = 1 } END { exit !found }' "$PORT_REGISTRY"; then
      continue
    fi
    port_in_use "$candidate" && continue
    PORT="$candidate"
    break
  done
  [ -n "$PORT" ] || fail "No free port left in $PORT_RANGE."

  if [ "$DRY_RUN" = true ]; then
    echo "Would reserve port $PORT for $APP_NAME in $PORT_REGISTRY"
  else
    printf '%s %s  # reserved %s by the Guess-Warrior deploy pipeline\n' "$APP_NAME" "$PORT" "$(date -u +%Y-%m-%d)" \
      | $SUDO tee -a "$PORT_REGISTRY" >/dev/null
    echo "Reserved port $PORT for $APP_NAME in $PORT_REGISTRY"
  fi
fi

# ------------------------------------------------------------------- dry run
if [ "$DRY_RUN" = true ]; then
  log "Deploy plan (dry run, nothing changed)"
  echo "Release:   $RELEASE_ID"
  echo "App dir:   $APP_DIR"
  echo "Port:      $PORT"
  echo "Python:    $(python3 -V)"
  echo "Service:   $SERVICE ($(systemctl is-active "$SERVICE" 2>/dev/null || echo 'not installed yet'))"
  if [ "$MANAGE_NGINX" = true ] && [ -n "$DOMAIN" ]; then
    bash "$SCRIPT_DIR/configure-nginx.sh" "$DOMAIN" "$PORT" "$SHARED" --dry-run
  else
    echo "nginx:     not configured (APP_URL is not set)"
  fi
  rm -f "$ARCHIVE"
  exit 0
fi

mkdir -p "$RELEASES" "$SHARED/venvs" "$SHARED/hf-cache"

# ------------------------------------------------------------ shared settings
if [ ! -f "$SHARED/.env" ]; then
  log "First deploy: creating $SHARED/.env"
  umask 077
  cat > "$SHARED/.env" <<EOF
PORT=$PORT
FLASK_DEBUG=0
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
HF_HOME=$SHARED/hf-cache
EOF
  umask 022
fi

# The reserved port always wins over what .env says.
sed -i "s/^PORT=.*/PORT=$PORT/" "$SHARED/.env"
grep -q '^PORT=' "$SHARED/.env" || echo "PORT=$PORT" >> "$SHARED/.env"

# ------------------------------------------------------------ unpack release
log "Unpacking release $RELEASE_ID"
rm -rf "$RELEASE"
mkdir -p "$RELEASE"
tar -xzf "$ARCHIVE" -C "$RELEASE"
rm -f "$ARCHIVE"

# ------------------------------------------------------------- dependencies
REQ_HASH="$(sha256sum "$RELEASE/requirements.txt" | cut -c1-12)"
VENV="$SHARED/venvs/$REQ_HASH"

if [ ! -x "$VENV/bin/gunicorn" ]; then
  log "Creating virtualenv for requirements $REQ_HASH (first time for this requirements.txt)"
  rm -rf "$VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  # CPU-only torch: the default wheel bundles CUDA and is several GB.
  "$VENV/bin/pip" install --quiet torch --index-url https://download.pytorch.org/whl/cpu
  "$VENV/bin/pip" install --quiet -r "$RELEASE/requirements.txt" \
    || { rm -rf "$VENV"; fail "pip install failed."; }
else
  echo "Reusing virtualenv $REQ_HASH"
fi
ln -sfn "$VENV" "$RELEASE/.venv"

# ----------------------------------------------------------- systemd service
UNIT="$(cat <<EOF
# Managed by the Guess-Warrior deploy pipeline (deploy/remote-deploy.sh).
[Unit]
Description=Guess-Warrior (Family Feud game)
After=network.target

[Service]
User=$(id -un)
WorkingDirectory=$APP_DIR/current
EnvironmentFile=$SHARED/.env
ExecStart=$APP_DIR/current/.venv/bin/gunicorn --worker-class gthread --workers 1 --threads 100 --timeout 120 --bind 127.0.0.1:\${PORT} wsgi:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
)"

if ! $SUDO test -f "$SERVICE_FILE" || [ "$(printf '%s\n' "$UNIT")" != "$($SUDO cat "$SERVICE_FILE")" ]; then
  log "Installing $SERVICE_FILE"
  printf '%s\n' "$UNIT" | $SUDO tee "$SERVICE_FILE" >/dev/null
  $SUDO systemctl daemon-reload
  $SUDO systemctl enable "$SERVICE" >/dev/null 2>&1
fi

# ------------------------------------------------------------------ switch
PREVIOUS=""
[ -L "$APP_DIR/current" ] && PREVIOUS="$(readlink "$APP_DIR/current")"

switch_to() {
  ln -sfn "$1" "$APP_DIR/current.tmp"
  mv -T "$APP_DIR/current.tmp" "$APP_DIR/current"
  $SUDO systemctl restart "$SERVICE"
}

# Startup loads the sentence-transformers model (and downloads it on the very
# first deploy), so allow a few minutes.
healthy() {
  for _ in $(seq 1 90); do
    if curl -fsS "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

log "Starting release $RELEASE_ID on port $PORT"
switch_to "$RELEASE"

log "Health check"
if ! healthy; then
  $SUDO journalctl -u "$SERVICE" -n 40 --no-pager || true

  if [ -n "$PREVIOUS" ] && [ -d "$PREVIOUS" ]; then
    log "Health check failed; rolling back to $(basename "$PREVIOUS")"
    switch_to "$PREVIOUS"
    healthy && echo "Rolled back; the previous release is serving traffic."
  fi

  fail "Release $RELEASE_ID did not pass its health check."
fi

# ---------------------------------------------------------------------- nginx
if [ "$MANAGE_NGINX" = true ] && [ -n "$DOMAIN" ]; then
  bash "$SCRIPT_DIR/configure-nginx.sh" "$DOMAIN" "$PORT" "$SHARED"
else
  log "APP_URL is not set: skipping nginx. Set the APP_URL repository variable once the subdomain exists."
fi

# ------------------------------------------------------------------- cleanup
# shellcheck disable=SC2012
ls -1dt "$RELEASES"/*/ | tail -n +"$((KEEP_RELEASES + 1))" | xargs -r rm -rf

# Keep the virtualenvs that kept releases still point at, plus the newest few.
IN_USE="$(for r in "$RELEASES"/*/; do readlink "$r.venv" 2>/dev/null; done | sort -u)"
# shellcheck disable=SC2012
ls -1dt "$SHARED"/venvs/*/ 2>/dev/null | tail -n +"$((KEEP_VENVS + 1))" | while read -r v; do
  v="${v%/}"
  printf '%s\n' "$IN_USE" | grep -qx "$v" || rm -rf "$v"
done

log "Deployed $RELEASE_ID"
echo "App: http://127.0.0.1:$PORT   Public: ${APP_URL:-not set}   Service: $SERVICE"
