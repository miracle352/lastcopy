#!/bin/bash
# Fresh isolated cloud Central only; never migrate/delete an existing database.
set -euo pipefail
export COMPOSE_PARALLEL_LIMIT=1
host=${1:?Central HTTPS hostname required}
[[ $host =~ ^central-[0-9-]+\.sslip\.io$ ]]
cd /srv/lastcopy
test ! -e central
git clone https://github.com/getodk/central.git central
cd central
git checkout 7d6de621955c5bb6a68e098ca10c9cbb92285cdf
git submodule update --init --recursive
test -z "$(sudo docker volume ls -q --filter label=com.docker.compose.project=lastcopy-cloud-odk)"
printf '%s\n' 'Fresh isolated database; no legacy upgrade.' > files/allow-postgres14-upgrade
umask 077
printf 'DOMAIN=%s\nSYSADMIN_EMAIL=coordinator@example.invalid\nSSL_TYPE=upstream\nHTTP_PORT=8384\nHTTPS_PORT=443\nSENTRY_TRACE_RATE=0\nSERVICE_NODE_OPTIONS=--max-old-space-size=384\nDB_POOL_SIZE=5\n' "$host" > .env
cat > lastcopy.cloud.yml <<'EOF'
services:
  nginx:
    ports: !override
      - 127.0.0.1:8384:80
    extra_hosts:
      - "o130137.ingest.sentry.io:127.0.0.1"
  service:
    mem_limit: 768m
  enketo:
    mem_limit: 768m
  postgres14:
    mem_limit: 512m
EOF
sudo docker compose -p lastcopy-cloud-odk -f docker-compose.yml -f lastcopy.cloud.yml build postgres postgres14 secrets service nginx enketo
# Upstream's one-shot detects an empty legacy volume and writes its own
# initialization marker. Do not manufacture the marker or remove old data.
sudo docker compose -p lastcopy-cloud-odk -f docker-compose.yml -f lastcopy.cloud.yml up -d --no-deps postgres
test "$(sudo docker wait lastcopy-cloud-odk-postgres-1)" = 0
sudo docker compose -p lastcopy-cloud-odk -f docker-compose.yml -f lastcopy.cloud.yml up -d --no-deps secrets postgres14 mail pyxform enketo_redis_main enketo_redis_cache enketo service nginx
printf '%s\n' 'Central containers started; HTTPS/authentication/readback acceptance still required.' > /srv/lastcopy/CENTRAL_BUILD_STATUS.txt
