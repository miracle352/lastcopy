#!/bin/bash
# Fresh LastCopy Ubuntu host only. No secrets or application data in user data.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
test "$(id -u)" = 0
. /etc/os-release
test "$ID" = ubuntu
test "$VERSION_ID" = 24.04
apt-get -o DPkg::Lock::Timeout=180 update
apt-get -o DPkg::Lock::Timeout=180 -y upgrade
apt-get -o DPkg::Lock::Timeout=180 install -y --no-install-recommends ca-certificates curl git unzip docker.io docker-compose-v2
systemctl enable --now docker
usermod -aG docker ubuntu
install -d -m 0750 -o ubuntu -g ubuntu /srv/lastcopy
install -d -m 0700 -o ubuntu -g ubuntu /srv/lastcopy/private
cat > /etc/ssh/sshd_config.d/70-lastcopy-key-only.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
sshd -t
systemctl reload ssh
printf '%s\n' 'OS bootstrap complete. Application is not deployed; no preservation/integration success claimed.' > /srv/lastcopy/BOOTSTRAP_STATUS.txt
chown ubuntu:ubuntu /srv/lastcopy/BOOTSTRAP_STATUS.txt
