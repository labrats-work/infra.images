#!/bin/sh
set -e
echo "Testing terraform image..."
terraform version
git --version
jq --version
yq --version
echo "All tests passed!"
