#!/bin/sh
set -e
echo "Testing ci-tools image..."
shellcheck --version
hadolint --version
actionlint --version
yamllint --version
make --version
jq --version
echo "All tests passed!"
