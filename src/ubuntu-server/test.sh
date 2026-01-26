#!/bin/sh
set -e
curl --version
git --version
ssh -V
jq --version
yq --version
ping -c 1 127.0.0.1
