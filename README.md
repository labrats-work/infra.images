# infra.images

Infrastructure container images with declarative tool management via `tools.yaml`.

## Available Images

| Image | Description | Base | Multi-arch |
|-------|-------------|------|------------|
| **ansible** | Ansible with git, ssh, jq, yq | Alpine 3.22 | ✅ |
| **terraform** | Terraform 1.13.4 with git, ssh, jq, yq | Alpine 3.22 | ✅ |
| **python** | Python 3.12 with pip | Debian Bookworm | ✅ |
| **python-ffmpeg** | Python 3.12 with ffmpeg | Debian Bookworm | ✅ |
| **omnibus** | All-in-one ops image | Alpine 3.22 | ✅ |
| **k8s-tools** | kubectl, helm, kustomize, flux, sops, age | Alpine 3.22 | ✅ |
| **ci-tools** | shellcheck, hadolint, actionlint, yamllint | Alpine 3.22 | ✅ |
| **arc-runner** | GitHub ARC runner with Claude CLI | actions-runner | ❌ |
| **alpine-hardened** | Security-hardened Alpine base | Alpine 3.22 | ✅ |

## Quick Start

```bash
# Pull an image
docker pull ghcr.io/labrats-work/infra.images/ansible:1.0.0

# Run a command
docker run --rm ghcr.io/labrats-work/infra.images/ansible:1.0.0 ansible --version
```

## Declarative Tool Management

Each image is defined by a `tools.yaml` file that specifies:
- Base image
- Package manager (apk/apt)
- Multi-arch support
- Tools to install

### tools.yaml Format

```yaml
base: docker.io/alpine:3.22
package_manager: apk
multi_arch: true
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

## Build Process

The workflow automatically:
1. Detects which images changed
2. Generates Dockerfiles from tools.yaml
3. Builds images in parallel (matrix)
4. Pushes to GHCR with semantic version tags
5. Generates SBOMs for security scanning
6. Runs tests for each image

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

# Build locally
docker build -t ansible:local src/ansible

# Test
docker run --rm ansible:local ansible --version
```

## Architecture

```
infra.images/
├── generate-dockerfile.py    # Dockerfile generator
├── src/
│   ├── ansible/
│   │   ├── tools.yaml        # Tool definitions
│   │   ├── dockerfile        # Auto-generated
│   │   └── test.sh           # Optional tests
│   ├── terraform/
│   ├── python/
│   ├── python-ffmpeg/
│   ├── omnibus/
│   └── arc-runner/
└── .github/workflows/
    └── build.yml             # Unified build workflow
```
