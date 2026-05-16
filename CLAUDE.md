# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Infrastructure container images with declarative tool management via `tools.yaml`. All images published to `ghcr.io/labrats-work/infra.images/<image>`.

## Architecture

```
infra.images/
├── generate-dockerfile.py    # Generates dockerfile from tools.yaml
├── find-dependents.py        # Dependency resolver for recursive builds
└── src/<image>/
    ├── tools.yaml            # Declarative tool definitions
    ├── dockerfile            # Auto-generated (do not edit)
    └── test.sh               # Optional
```

## tools.yaml Schema

```yaml
base: docker.io/alpine:3.22   # External or ghcr.io/labrats-work/infra.images/<name>:main
package_manager: apk          # apk | apt
multi_arch: true              # Build for amd64 + arm64
build_args:
  - name: VERSION
    default: "1.0.0"
tools:
  - name: git
    method: package           # package | binary | script
    package: git
```

## Recursive Build System

`build.yml` is dependency-driven:

1. **detect-changes** identifies root images to build (those with external bases)
2. **build-roots** builds them in a matrix
3. After each root image is built + pushed + tested, `find-dependents.py --from-image <name>` finds dependents
4. If dependents exist, dispatches a child workflow via `gh workflow run` — child resolves dependents, builds them, and recursively dispatches its own children
5. Parent jobs block on child workflows, propagating failures upward

## Image Dependency Tree

Root images have external bases. Derived images reference `ghcr.io/labrats-work/infra.images/<name>:main`.

- `alpine:3.22` → `alpine-hardened` → ansible, ci-tools, k8s-tools, omnibus, terraform
- `ubuntu:24.04` → `ubuntu-hardened` → ubuntu-server, ubuntu-workstation
- `debian:12-slim` → `debian-hardened`
- `python:3.12-slim` → python, python-ffmpeg

## Rules

- Do **not** edit `dockerfile` directly — it's auto-generated
- Do **not** use `latest` tag in production
- Use full registry path as the dependency needle (`ghcr.io/labrats-work/infra.images/<name>:`), never `/<name>:` alone (avoids self-matching)
- All images share the same version (monorepo)

## Local Development

```bash
python3 generate-dockerfile.py --image ansible
docker build -t ansible:local src/ansible
python3 find-dependents.py --roots
python3 find-dependents.py --from-image alpine-hardened
```
