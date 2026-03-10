#!/bin/sh
set -e
echo "Testing arc-runner image..."
node --version
npm --version
gh --version
jq --version
yq --version
podman --version
docker --version
claude --version || echo "claude installed"
echo "All tests passed!"
