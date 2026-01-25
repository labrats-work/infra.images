#!/bin/sh
set -e
echo "Testing ansible image..."
ansible --version
git --version
ssh -V
jq --version
yq --version
echo "All tests passed!"
