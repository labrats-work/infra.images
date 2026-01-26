# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Overview

Infrastructure container images with declarative tool management via `tools.yaml`. All images are published to `ghcr.io/labrats-work/infra.images/<image>`.

## Architecture

```
infra.images/
├── generate-dockerfile.py    # Generates dockerfile from tools.yaml
├── find-dependents.py        # Dependency resolver for recursive builds
├── src/
│   └── <image>/
│       ├── tools.yaml        # Declarative tool definitions
│       ├── dockerfile        # Auto-generated (do not edit)
│       └── test.sh           # Optional test script
└── .github/workflows/
    └── build.yml             # Recursive dependency-driven build workflow
```

## Key Concepts

### tools.yaml Schema

```yaml
base: docker.io/alpine:3.22   # Base image
package_manager: apk          # apk or apt
multi_arch: true              # Build for amd64 and arm64
workdir: /app                 # Working directory
user: runner                  # Switch back to user (optional)
entrypoint: '["cmd"]'         # Custom entrypoint (optional)

build_args:                   # Build-time arguments
  - name: VERSION
    default: "1.0.0"

tools:
  - name: git
    method: package           # Use package manager
    package: git

  - name: yq
    method: binary            # Download binary
    url: https://...
    dest: /usr/local/bin/yq

  - name: terraform
    method: script            # Custom install script
    script: |
      curl -LO https://...
      unzip ...
```

### Recursive Build System

The CI workflow (`build.yml`) uses a dependency-driven recursive build:

1. **Orchestrator mode** (push/PR/tag): `detect-changes` identifies root images to build, then `build-roots` builds them in a matrix
2. **Per-image dispatch**: After each root image is built+pushed+tested, it runs `find-dependents.py --from-image <name>` to find dependents
3. **Recursive dispatch**: If dependents exist, `gh workflow run build.yml -f from_image=<name>:<sha-tag>` dispatches a child workflow
4. **Child workflow**: Resolves dependents, builds them in a matrix, and each job dispatches its own dependents (recurse)
5. **Wait-for-completion**: Parent jobs block until child workflows finish, propagating failures upward

Key scripts:
- `find-dependents.py --from-image <name>` — returns JSON array of images whose `base:` references `<name>`
- `find-dependents.py --roots` — returns images with external bases (not from this repo's registry)

### Image Dependency Tree

Root images have external bases. Derived images reference this repo's registry (`ghcr.io/labrats-work/infra.images/<name>:main`).

- `alpine:3.22` → `alpine-hardened` → ansible, ci-tools, k8s-tools, omnibus, terraform
- `ubuntu:24.04` → `ubuntu-hardened` → ubuntu-server, ubuntu-workstation
- `debian:12-slim` → `debian-hardened`
- `python:3.12-slim` → python, python-ffmpeg
- `actions-runner:latest` → arc-runner

## Common Operations

### Add a Tool to Existing Image

```bash
# Edit the tools.yaml
vim src/ansible/tools.yaml

# Add tool entry
# - name: newtool
#   method: package
#   package: newtool

# Commit with conventional commit
git add src/ansible/tools.yaml
git commit -m "feat(ansible): add newtool"
git push
```

### Create New Image

```bash
mkdir src/myimage
# Create src/myimage/tools.yaml with base, package_manager, tools
# Optionally create src/myimage/test.sh
git add src/myimage
git commit -m "feat: add myimage"
git push
```

To create a **derived** image, set the base to an image from this repo:
```yaml
base: ghcr.io/labrats-work/infra.images/alpine-hardened:main
```

The build system detects the dependency automatically via `find-dependents.py`.

### Create Release

```bash
git tag 1.1.0
git push origin 1.1.0
```

### Local Development

```bash
# Generate dockerfile
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

## Versioning

- All images share the same version (monorepo)
- Tags without `v` prefix: `1.0.0` not `v1.0.0`
- Conventional commits: `feat:`, `fix:`, `chore:`

## Images Reference

| Image | Purpose | Base | Key Tools |
|-------|---------|------|-----------|
| alpine-hardened | Security-hardened Alpine base | alpine:3.22 | hardening scripts |
| debian-hardened | Security-hardened Debian base | debian:12-slim | hardening scripts |
| ubuntu-hardened | Security-hardened Ubuntu base | ubuntu:24.04 | hardening scripts |
| ansible | Configuration management | alpine-hardened | ansible, git, ssh, jq, yq |
| terraform | Infrastructure provisioning | alpine-hardened | terraform, git, jq, yq |
| omnibus | All-in-one operations | alpine-hardened | ansible, terraform, python, wireguard |
| k8s-tools | Kubernetes management | alpine-hardened | kubectl, helm, kustomize, flux, sops |
| ci-tools | CI/CD linting | alpine-hardened | shellcheck, hadolint, actionlint |
| ubuntu-server | Server utilities | ubuntu-hardened | curl, git, ssh, jq, yq, net-tools |
| ubuntu-workstation | XFCE desktop with VNC | ubuntu-hardened | xfce4, tigervnc, novnc, firefox |
| python | Python applications | python:3.12-slim | python3, pip |
| python-ffmpeg | Media processing | python:3.12-slim | python3, pip, ffmpeg |
| arc-runner | GitHub Actions runner | actions-runner | gh, node, podman, claude |

## Do Not

- Edit `dockerfile` directly (it's auto-generated)
- Use `latest` tag in production
- Add secrets or credentials
- Change base images without testing multi-arch compatibility
- Use `/<name>:` as a needle for dependency matching (use full registry path to avoid self-matching)
