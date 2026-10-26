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
  --recipient /srv/lastcopy/backup-recipient.pem --output "$folder/$name" --include-enketo
chown ubuntu:ubuntu "$folder/$name" "$folder/${name%.cms}.receipt.json"
python3 /srv/lastcopy/source/scripts/backup_health.py --path "$health" --state success --receipt "$folder/${name%.cms}.receipt.json"
trap - ERR
if [[ -f /srv/lastcopy/private/backup-uploader.json ]]; then
  /srv/lastcopy/ops/bin/python /srv/lastcopy/source/scripts/backup_offsite.py \
    --folder "$folder" --credentials /srv/lastcopy/private/backup-uploader.json \
    --health /srv/lastcopy/private/application/operations/offsite.json
fi
# User approved daily copies without deletion; storage grows until the reserve gate.
