# ADR-0005: Reject DevSec Ansible Hardening for Containers

## Status

Accepted

## Date

2026-02-20

## Context

We need security hardening for our container base images (alpine-hardened, debian-hardened, ubuntu-hardened). The DevSec `os_hardening` Ansible role is a well-known option for host-level hardening, but we evaluated it against our container use case.

## Decision

We reject the DevSec Ansible hardening approach for containers and instead implement container-native hardening scripts directly in `tools.yaml`.

## Reasons for Rejection

1. **Alpine unsupported**: DevSec `os_hardening` does not support Alpine Linux, which is our primary base image.

2. **Incompatible with Docker build**: The role requires sysctl, systemd, auditd, and PAM, none of which can run during `docker build`. Containers share the host kernel and do not manage their own init system.

3. **Designed for hosts, not containers**: The role assumes a full operating system lifecycle (boot, services, kernel parameters). Containers are ephemeral, single-process environments where most of these controls are irrelevant or must be applied at runtime via the container runtime (e.g., `--security-opt`, seccomp profiles, AppArmor).

4. **Image bloat**: Installing Ansible and the role's dependencies adds ~200MB to the image, defeating the purpose of slim base images.

5. **Build complexity**: Ansible requires Python, which is not present in Alpine slim or Debian slim images. Adding it solely for hardening creates unnecessary dependency chains.

## Container-Native Hardening (Chosen Approach)

Our hardening scripts in each `*-hardened` image's `tools.yaml` implement CIS-aligned controls that are applicable at build time:

- Remove SUID/SGID binaries
- Restrict file permissions (`/etc/shadow`, `/etc/gshadow`)
- Remove world-writable file permissions
- Set sticky bit on world-writable directories
- Remove unnecessary system users (games, news, uucp, etc.)
- Remove cron directories
- Delete legacy auth files (`.netrc`, `.rhosts`, `.forward`)
- Empty `/etc/securetty` to prevent root console login
- Disable core dumps via `limits.d`
- Set restrictive umask (027)
- Remove SSH host keys (generated at runtime)
- Create nonroot user (UID 65532) for application workloads

Runtime-level controls (seccomp, AppArmor, read-only rootfs, no-new-privileges) are applied by the container orchestrator, not baked into the image.

## Consequences

- Each hardened base image carries its own hardening script tailored to the package manager (apk vs apt).
- Hardening is transparent and auditable via `tools.yaml` and the generated Dockerfile.
- No external Ansible dependency in the build chain.
- Security posture is validated by `test.sh` scripts that check for SUID/SGID binaries, file permissions, and user existence.
