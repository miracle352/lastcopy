#!/bin/bash
set -euo pipefail
test "$(id -u)" = 0
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-install-recommends debian-keyring debian-archive-keyring apt-transport-https curl gpg
curl --fail --silent --show-error --location https://dl.cloudsmith.io/public/caddy/stable/gpg.key -o /tmp/caddy-stable-key
gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg /tmp/caddy-stable-key
curl --fail --silent --show-error --location https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt -o /etc/apt/sources.list.d/caddy-stable.list
chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y --no-install-recommends caddy
cat > /etc/caddy/Caddyfile <<'EOF'
api-18-141-113-136.sslip.io {
  request_body {
    max_size 11MB
  }
  header {
    X-Content-Type-Options nosniff
    Referrer-Policy no-referrer
    Cache-Control no-store
  }
  reverse_proxy 127.0.0.1:8000 {
    header_up Host localhost
  }
}
central-18-141-113-136.sslip.io {
  reverse_proxy 127.0.0.1:8384
}
app-18-141-113-136.sslip.io {
  request_body {
    max_size 11MB
  }
  reverse_proxy 127.0.0.1:3000
}
EOF
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
caddy version > /srv/lastcopy/CADDY_VERSION.txt
