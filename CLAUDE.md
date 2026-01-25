# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Overview

Infrastructure container images with declarative tool management via `tools.yaml`. All images are published to `ghcr.io/labrats-work/infra.images/<image>`.

## Architecture

```
infra.images/
├── generate-dockerfile.py    # Generates dockerfile from tools.yaml
├── src/
│   └── <image>/
│       ├── tools.yaml        # Declarative tool definitions
│       ├── dockerfile        # Auto-generated (do not edit)
│       └── test.sh           # Optional test script
└── .github/workflows/
    └── build.yml             # Unified matrix build workflow
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

### Build Process

1. Workflow detects which `src/*/tools.yaml` changed
2. Runs `generate-dockerfile.py` to create dockerfile
3. Builds images in parallel (matrix strategy)
4. Multi-arch images use QEMU emulation
5. Pushes to GHCR with semantic version tags

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
# Create directory
mkdir src/myimage

# Create tools.yaml
cat > src/myimage/tools.yaml << 'EOF'
base: docker.io/alpine:3.22
package_manager: apk
multi_arch: true
workdir: /app

tools:
  - name: mytool
    method: package
    package: mytool
EOF

# Optional: add test script
cat > src/myimage/test.sh << 'EOF'
#!/bin/sh
set -e
mytool --version
EOF

# Commit
git add src/myimage
git commit -m "feat: add myimage"
git push
```

### Create Release

```bash
# Create semantic version tag (no v prefix)
git tag 1.1.0
git push origin 1.1.0
```

### Generate Dockerfile Locally

```bash
python3 generate-dockerfile.py --image ansible
cat src/ansible/dockerfile
```

## Versioning

- All images share the same version (monorepo)
- Tags without `v` prefix: `1.0.0` not `v1.0.0`
- Conventional commits: `feat:`, `fix:`, `chore:`

## Images Reference

| Image | Purpose | Key Tools |
|-------|---------|-----------|
| ansible | Configuration management | ansible, git, ssh, jq, yq |
| terraform | Infrastructure provisioning | terraform, git, jq, yq |
| python | Python applications | python3, pip |
| python-ffmpeg | Media processing | python3, pip, ffmpeg |
| omnibus | All-in-one operations | ansible, terraform, python, wireguard |
| k8s-tools | Kubernetes management | kubectl, helm, kustomize, flux, sops |
| ci-tools | CI/CD linting | shellcheck, hadolint, actionlint |
| arc-runner | GitHub Actions runner | gh, node, podman, claude |

## Do Not

- Edit `dockerfile` directly (it's auto-generated)
- Use `latest` tag in production
- Add secrets or credentials
- Change base images without testing multi-arch compatibility
