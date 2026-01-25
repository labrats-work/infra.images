#!/bin/sh
set -e
echo "Testing k8s-tools image..."
kubectl version --client
helm version
kustomize version
flux --version
sops --version
age --version
jq --version
yq --version
echo "All tests passed!"
