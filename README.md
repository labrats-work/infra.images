# infra.images

Infrastructure container images with declarative tool management via `tools.yaml`.

## Available Images

| Image | Description | Base | Multi-arch |
|-------|-------------|------|------------|
| **alpine-hardened** | Security-hardened Alpine base | Alpine 3.22 | amd64, arm64 |
| **debian-hardened** | Security-hardened Debian base | Debian 12 | amd64, arm64 |
| **ubuntu-hardened** | Security-hardened Ubuntu base | Ubuntu 24.04 | amd64, arm64 |
| **ansible** | Ansible with git, ssh, jq, yq | alpine-hardened | amd64, arm64 |
| **terraform** | Terraform with git, ssh, jq, yq | alpine-hardened | amd64, arm64 |
| **omnibus** | All-in-one ops image | alpine-hardened | amd64, arm64 |
| **k8s-tools** | kubectl, helm, kustomize, flux, sops, age | alpine-hardened | amd64, arm64 |
| **ci-tools** | shellcheck, hadolint, actionlint, yamllint | alpine-hardened | amd64, arm64 |
| **ubuntu-server** | Server utilities, networking, editors | ubuntu-hardened | amd64, arm64 |
| **ubuntu-workstation** | XFCE desktop with VNC/noVNC access | ubuntu-hardened | amd64 |
| **python** | Python 3.12 with pip | Python 3.12 slim | amd64, arm64 |
| **python-ffmpeg** | Python 3.12 with ffmpeg | Python 3.12 slim | amd64, arm64 |
| **arc-runner** | GitHub ARC runner with Claude CLI | actions-runner | amd64 |

## Quick Start

```bash
# Pull an image
docker pull ghcr.io/labrats-work/infra.images/ansible:1.0.0

# Run a command
docker run --rm ghcr.io/labrats-work/infra.images/ansible:1.0.0 ansible --version

# Run the workstation with VNC
docker run -d -p 6080:6080 -e VNC_PASSWORD=secret \
  ghcr.io/labrats-work/infra.images/ubuntu-workstation:main \
  start-vnc
# Open http://localhost:6080 in your browser
```

## Image Dependency Tree

Images form a dependency tree. When a base image is rebuilt, all its dependents are
automatically rebuilt with the new base, recursively, until every leaf is reached.

```mermaid
graph TD
    A1[alpine:3.22] --> AH[alpine-hardened]
    AH --> ansible
    AH --> ci-tools
    AH --> k8s-tools
    AH --> omnibus
    AH --> terraform

    U1[ubuntu:24.04] --> UH[ubuntu-hardened]
    UH --> ubuntu-server
    UH --> ubuntu-workstation

    D1[debian:12-slim] --> DH[debian-hardened]

    P1[python:3.12-slim] --> python
    P1 --> python-ffmpeg

    R1[actions-runner:latest] --> arc-runner
```

**Root** images have external bases (not from this repo). **Leaf** images have no
dependents. The tree can be extended to arbitrary depth.

## Recursive Build System

The CI workflow (`build.yml`) uses a dependency-driven recursive build. The script
`find-dependents.py` scans `tools.yaml` files to resolve the tree at runtime.
Each root image builds in parallel, then dispatches child workflows for its dependents,
recursively, until every leaf is reached.

See [docs/recursive-build-system.md](docs/recursive-build-system.md) for the full
description with diagrams, pros/cons, and compliance check guidance.

## Declarative Tool Management

Each image is defined by a `tools.yaml` file that specifies:
- Base image and package manager
- Multi-arch support (amd64, arm64)
- Tools to install via three methods

### tools.yaml Format

```yaml
base: docker.io/alpine:3.22       # or ghcr.io/labrats-work/infra.images/alpine-hardened:main
package_manager: apk               # apk or apt
multi_arch: true                   # build for amd64 and arm64
workdir: /app

build_args:
  - name: VERSION
    default: "1.0.0"

tools:
  # Package install
  - name: git
    description: Version control
    method: package
    package: git

  # Binary download
  - name: yq
    description: YAML processor
    method: binary
    url: https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
    dest: /usr/local/bin/yq

  # Custom script
  - name: terraform
    description: Infrastructure as Code
    method: script
    script: |
      curl -LO https://releases.hashicorp.com/terraform/${VERSION}/terraform_${VERSION}_linux_amd64.zip
      unzip terraform_${VERSION}_linux_amd64.zip -d /usr/local/bin
```

## Adding a New Tool

1. Edit the appropriate `src/<image>/tools.yaml`
2. Add the tool with method: `package`, `binary`, or `script`
3. Commit and push
4. Create a version tag: `git tag 1.1.0 && git push origin 1.1.0`

## Adding a New Image

1. Create directory: `mkdir src/myimage`
2. Create `src/myimage/tools.yaml` with configuration
3. Optionally add `src/myimage/test.sh` for testing
4. Commit and push

To create a **derived** image, set the base to an image from this repo:
```yaml
base: ghcr.io/labrats-work/infra.images/ubuntu-hardened:main
```

The build system will automatically detect the dependency and rebuild your
image whenever its base is updated.

## Versioning

All images share the same version (monorepo style):
- `1.0.0` - Full version
- `1.0` - Major.minor
- `1` - Major only
- `sha-abc1234` - Commit SHA

## Local Development

```bash
# Generate Dockerfile for an image
python3 generate-dockerfile.py --image ansible
cat src/ansible/dockerfile

# Build locally
docker build -t ansible:local src/ansible

# Test
docker run --rm ansible:local ansible --version

# Check dependency tree
python3 find-dependents.py --roots
python3 find-dependents.py --from-image alpine-hardened
```

## Architecture

```
infra.images/
+-- generate-dockerfile.py    # Dockerfile generator from tools.yaml
+-- find-dependents.py        # Dependency resolver for build ordering
+-- src/
|   +-- <image>/
|       +-- tools.yaml        # Declarative tool definitions
|       +-- dockerfile        # Auto-generated (do not edit)
|       +-- test.sh           # Optional test script
+-- .github/workflows/
    +-- build.yml             # Recursive dependency-driven build workflow
```
