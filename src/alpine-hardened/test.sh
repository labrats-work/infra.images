#!/bin/sh
set -e
echo "Testing alpine-hardened image..."

# Check hardened version file exists
cat /etc/hardened-version

# Check no SUID/SGID binaries
suid_count=$(find / -xdev -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | wc -l)
if [ "$suid_count" -gt 0 ]; then
    echo "FAIL: Found $suid_count SUID/SGID binaries"
    exit 1
fi
echo "PASS: No SUID/SGID binaries"

# Check nonroot user exists
id nonroot
echo "PASS: nonroot user exists"

# Check shadow file permissions
perms=$(stat -c %a /etc/shadow)
if [ "$perms" != "600" ]; then
    echo "FAIL: /etc/shadow has permissions $perms (expected 600)"
    exit 1
fi
echo "PASS: /etc/shadow permissions correct"

echo "All hardening tests passed!"
