#!/bin/sh
set -e
echo "=== node-hardened image test ==="
node --version
npm --version
git --version
curl --version | head -1
jq --version
tini --version
echo "All checks passed"
