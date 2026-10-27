#!/bin/bash
# Operator-approved existing host only. No passwords, keys or data are exported.
set -euo pipefail
test "$(id -u)" = 0
. /etc/os-release
test "$ID:$VERSION_ID" = ubuntu:24.04
test ! -e /etc/ssh/sshd_config.d/10-lastcopy-stack-hardening.conf
test "$(ufw status | head -n 1)" = 'Status: inactive'
test -x /usr/sbin/sshd
install -d -m 0700 /srv/lastcopy/stack-review/host
cat > /srv/lastcopy/stack-review/host/rollback.sh <<'EOF'
#!/bin/bash
set -eu
rm -f /etc/ssh/sshd_config.d/10-lastcopy-stack-hardening.conf
/usr/sbin/sshd -t
systemctl reload ssh
ufw --force disable
EOF
chmod 0700 /srv/lastcopy/stack-review/host/rollback.sh
systemd-run --unit=lastcopy-host-guard --on-active=5m /srv/lastcopy/stack-review/host/rollback.sh
trap '/srv/lastcopy/stack-review/host/rollback.sh' ERR
cat > /etc/ssh/sshd_config.d/10-lastcopy-stack-hardening.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
X11Forwarding no
MaxAuthTries 3
EOF
/usr/sbin/sshd -t
/usr/sbin/sshd -T | grep -x 'permitrootlogin no'
/usr/sbin/sshd -T | grep -x 'passwordauthentication no'
systemctl reload ssh
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw default deny incoming
ufw default allow outgoing
ufw --force enable
printf '%s\n' 'Rollback timer active. Verify fresh SSH/HTTPS before cancelling lastcopy-host-guard.timer. Reboot is a separate approved step.'
