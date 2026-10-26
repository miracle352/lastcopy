#!/usr/bin/env bash
set -euo pipefail
umask 077
folder=/srv/lastcopy/backups
health=/srv/lastcopy/private/application/operations/backup.json
python3 /srv/lastcopy/source/scripts/backup_health.py --path "$health" --state running
trap 'python3 /srv/lastcopy/source/scripts/backup_health.py --path "$health" --state failed' ERR
install -d -m 700 -o ubuntu -g ubuntu "$folder"
name="lastcopy-db-$(date -u +%Y%m%dT%H%M%SZ).cms"
python3 /srv/lastcopy/source/scripts/backup_databases.py \
  --store /srv/lastcopy/private/application \
  --recipient /srv/lastcopy/backup-recipient.pem --output "$folder/$name"
chown ubuntu:ubuntu "$folder/$name" "$folder/${name%.cms}.receipt.json"
python3 /srv/lastcopy/source/scripts/backup_health.py --path "$health" --state success --receipt "$folder/${name%.cms}.receipt.json"
# User approved daily copies without deletion; storage grows until the reserve gate.
