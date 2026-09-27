#!/usr/bin/env bash
# Points DOMAIN at the app on 127.0.0.1:PORT through the host's nginx.
#
#   configure-nginx.sh <domain> <port> <state-dir> [--dry-run]
#
# - Any other enabled nginx config that serves *only* this domain is moved to
#   /etc/nginx/disabled-by-guess-warrior/ (never deleted). A config that serves this
#   domain together with other sites is left alone and the script stops, so no
#   other site on the server is affected.
# - TLS: reuses the certificate the previous config used, else an existing
#   Let's Encrypt certificate for the domain, else requests one with certbot
#   (using the server's existing certbot account, or CERTBOT_EMAIL to register
#   one), else serves plain HTTP and warns.
# - Every change is checked with `nginx -t` before reload; on failure the
#   previous configuration is restored.

set -euo pipefail

DOMAIN="${1:?domain required}"
PORT="${2:?port required}"
STATE_DIR="${3:?state dir required}"
DRY_RUN=false
[ "${4:-}" = "--dry-run" ] && DRY_RUN=true

SITE_NAME="guess-warrior-${DOMAIN//./-}"
SITE_FILE="/etc/nginx/sites-available/$SITE_NAME.conf"
SITE_LINK="/etc/nginx/sites-enabled/$SITE_NAME.conf"
DISABLED_DIR="/etc/nginx/disabled-by-guess-warrior"
CERT_STATE="$STATE_DIR/nginx-cert.env"

log() { printf '\n==> %s\n' "$*"; }
warn() { printf '\nWARNING: %s\n' "$*" >&2; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  sudo -n true 2>/dev/null || fail "Configuring nginx needs root or passwordless sudo."
  SUDO="sudo -n"
fi

command -v nginx >/dev/null || fail "nginx is not installed on this server."
[ -d /etc/nginx/sites-enabled ] || fail "/etc/nginx/sites-enabled does not exist."

# The host nginx must be what answers on port 80, otherwise (for example with a
# Nginx Proxy Manager container) the files written here would never be used.
if ! $SUDO ss -ltnpH 'sport = :80' | grep -q '"nginx"'; then
  fail "Port 80 is not served by the host nginx ($($SUDO ss -ltnpH 'sport = :80' | head -n 1)). Not touching nginx."
fi

# ------------------------------------------------ configs serving this domain
# Prints each enabled config file (other than ours) whose server_name lists DOMAIN.
find_domain_configs() {
  local file
  for file in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
    [ -e "$file" ] || continue
    [ "$(basename "$file")" = "$SITE_NAME.conf" ] && continue
    if $SUDO grep -Eq "server_name[^;]*[[:space:]]${DOMAIN//./\\.}([[:space:]]|;)" "$file"; then
      echo "$file"
    fi
  done
}

# All names a config file answers to, one per line.
server_names_in() {
  $SUDO sed -n 's/^[[:space:]]*server_name[[:space:]]\{1,\}\([^;]*\);.*/\1/p' "$1" | tr -s ' \t' '\n' | sed '/^$/d' | sort -u
}

CONFLICTS="$(find_domain_configs || true)"
TO_DISABLE=""

for file in $CONFLICTS; do
  others="$(server_names_in "$file" | grep -vx "$DOMAIN" | grep -vx "www.$DOMAIN" || true)"
  if [ -n "$others" ]; then
    fail "$file serves $DOMAIN together with other sites ($(echo "$others" | tr '\n' ' ')). Remove $DOMAIN from it by hand, then re-run; nothing was changed."
  fi
  TO_DISABLE="$TO_DISABLE $file"
done

# ---------------------------------------------------------------- certificate
SSL_CERT=""
SSL_KEY=""

[ -f "$CERT_STATE" ] && . "$CERT_STATE"

if [ -z "$SSL_CERT" ]; then
  for file in $CONFLICTS; do
    cert="$($SUDO sed -n 's/^[[:space:]]*ssl_certificate[[:space:]]\{1,\}\([^;]*\);.*/\1/p' "$file" | head -n 1)"
    key="$($SUDO sed -n 's/^[[:space:]]*ssl_certificate_key[[:space:]]\{1,\}\([^;]*\);.*/\1/p' "$file" | head -n 1)"
    if [ -n "$cert" ] && [ -n "$key" ]; then
      SSL_CERT="$cert"
      SSL_KEY="$key"
      echo "Reusing the certificate from $file"
      break
    fi
  done
fi

if [ -z "$SSL_CERT" ] && $SUDO test -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
  SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
  SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
fi

if [ -n "$SSL_CERT" ] && ! $SUDO test -f "$SSL_CERT"; then
  warn "Certificate $SSL_CERT no longer exists; ignoring it."
  SSL_CERT=""
  SSL_KEY=""
fi

NEEDS_CERTBOT=false
if [ -z "$SSL_CERT" ]; then
  if command -v certbot >/dev/null; then
    NEEDS_CERTBOT=true
  else
    warn "No certificate for $DOMAIN and certbot is not installed: serving HTTP only."
  fi
fi

# ------------------------------------------------------------------ rendering
render_site() {
  local tls="$1"
  local ssl_options=""
  $SUDO test -f /etc/letsencrypt/options-ssl-nginx.conf && ssl_options="    include /etc/letsencrypt/options-ssl-nginx.conf;"

  cat <<EOF
# Managed by the Guess-Warrior deploy pipeline (deploy/configure-nginx.sh).
# Manual edits are overwritten on the next deploy.

map \$http_upgrade \$guess_warrior_connection_upgrade {
    default upgrade;
    ''      close;
}

EOF

  local proxy
  proxy="$(cat <<EOF
    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$guess_warrior_connection_upgrade;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 3600s;
    }
EOF
)"

  if [ "$tls" = true ]; then
    cat <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name $DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
$ssl_options

$proxy
}
EOF
  else
    cat <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

$proxy
}
EOF
  fi
}

TLS=false
[ -n "$SSL_CERT" ] && TLS=true

# ------------------------------------------------------------------- dry run
if [ "$DRY_RUN" = true ]; then
  log "nginx plan for $DOMAIN (dry run, nothing changed)"
  echo "Upstream:        127.0.0.1:$PORT"
  echo "Our site file:   $SITE_FILE"
  if [ -n "$TO_DISABLE" ]; then
    echo "Would disable:  $TO_DISABLE"
  else
    echo "Would disable:   nothing (no other config serves $DOMAIN)"
  fi
  if [ "$TLS" = true ]; then
    echo "Certificate:     $SSL_CERT"
  elif [ "$NEEDS_CERTBOT" = true ]; then
    echo "Certificate:     would request one with certbot"
  else
    echo "Certificate:     none, HTTP only"
  fi
  log "Config that would be written"
  render_site "$TLS"
  exit 0
fi

# ---------------------------------------------------------------------- apply
BACKUP_STAMP="$(date +%Y%m%d-%H%M%S)"
MOVED=""
PREVIOUS_SITE=""

restore() {
  warn "Restoring the previous nginx configuration."
  if [ -n "$PREVIOUS_SITE" ]; then
    $SUDO cp "$PREVIOUS_SITE" "$SITE_FILE"
  else
    $SUDO rm -f "$SITE_FILE" "$SITE_LINK"
  fi
  for pair in $MOVED; do
    $SUDO mv "${pair#*=}" "${pair%%=*}"
  done
  $SUDO nginx -t >/dev/null 2>&1 && $SUDO nginx -s reload
}

apply_site() {
  local tls="$1"
  local tmp
  tmp="$(mktemp)"
  render_site "$tls" > "$tmp"

  if $SUDO test -f "$SITE_FILE" && $SUDO cmp -s "$tmp" "$SITE_FILE" && [ -L "$SITE_LINK" ] && [ -z "$TO_DISABLE" ]; then
    rm -f "$tmp"
    echo "nginx config unchanged."
    return 0
  fi

  if $SUDO test -f "$SITE_FILE"; then
    PREVIOUS_SITE="$(mktemp)"
    $SUDO cp "$SITE_FILE" "$PREVIOUS_SITE"
  fi

  $SUDO mkdir -p "$DISABLED_DIR"
  for file in $TO_DISABLE; do
    target="$DISABLED_DIR/$(basename "$file").$BACKUP_STAMP"
    $SUDO mv "$file" "$target"
    MOVED="$MOVED $file=$target"
    echo "Disabled $file (moved to $target)"
  done
  TO_DISABLE=""

  $SUDO install -m 644 "$tmp" "$SITE_FILE"
  rm -f "$tmp"
  $SUDO ln -sfn "$SITE_FILE" "$SITE_LINK"

  if ! $SUDO nginx -t; then
    restore
    fail "nginx rejected the new configuration; the previous one was restored."
  fi

  $SUDO nginx -s reload
  echo "nginx reloaded: $DOMAIN -> 127.0.0.1:$PORT"
}

log "Configuring nginx for $DOMAIN"
$SUDO mkdir -p /var/www/html   # ACME http-01 challenge webroot
apply_site "$TLS"

if [ "$NEEDS_CERTBOT" = true ]; then
  log "Requesting a certificate for $DOMAIN"
  EMAIL_ARGS=""
  [ -n "${CERTBOT_EMAIL:-}" ] && EMAIL_ARGS="-m $CERTBOT_EMAIL"
  # shellcheck disable=SC2086
  if $SUDO certbot certonly --webroot -w /var/www/html -d "$DOMAIN" \
      --non-interactive --agree-tos $EMAIL_ARGS --keep-until-expiring; then
    SSL_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    apply_site true
  else
    warn "certbot could not issue a certificate; $DOMAIN stays on HTTP for now."
  fi
fi

if [ -n "$SSL_CERT" ]; then
  printf 'SSL_CERT=%q\nSSL_KEY=%q\n' "$SSL_CERT" "$SSL_KEY" > "$CERT_STATE"
fi

if [ -n "$MOVED" ]; then
  echo "Previous configs are kept in $DISABLED_DIR; move one back and reload nginx to undo."
fi
