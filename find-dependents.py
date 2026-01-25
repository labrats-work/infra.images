#!/usr/bin/env python3
"""
Find image dependents based on tools.yaml base references.

Usage:
    # Find images whose base: references "alpine-hardened"
    python3 find-dependents.py --from-image alpine-hardened
    # → ["ansible","ci-tools","k8s-tools","omnibus","terraform"]

    # Find root images (base: is external, not from our registry)
    python3 find-dependents.py --roots
    # → ["alpine-hardened","arc-runner","debian-hardened","python","python-ffmpeg","ubuntu-hardened"]
"""

import argparse
import json
import sys
from pathlib import Path

REGISTRY_PATH = "ghcr.io/labrats-work/infra.images/"


def get_base_field(tools_yaml: Path) -> str:
    """Extract the base: field from a tools.yaml file."""
    for line in tools_yaml.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("base:"):
            value = stripped.split(":", 1)[1].strip()
            # Strip YAML quotes
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            return value
    return ""


def scan_images(src: str) -> dict:
    """Return {image_name: base_field} for every image with a tools.yaml."""
    src_path = Path(src)
    images = {}
    for tools_yaml in sorted(src_path.glob("*/tools.yaml")):
        image_name = tools_yaml.parent.name
        base = get_base_field(tools_yaml)
        if base:
            images[image_name] = base
    return images


def find_dependents(from_image: str, src: str) -> list:
    """Return images whose base: contains /<from_image>:"""
    needle = f"/{from_image}:"
    images = scan_images(src)
    return sorted(name for name, base in images.items() if needle in base)


def find_roots(src: str) -> list:
    """Return images whose base: does NOT reference our registry."""
    images = scan_images(src)
    return sorted(name for name, base in images.items()
                  if REGISTRY_PATH not in base)


def main():
    parser = argparse.ArgumentParser(
        description="Find image dependents based on tools.yaml base references"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--from-image",
        help="Find images depending on this base image name"
    )
    group.add_argument(
        "--roots",
        action="store_true",
        help="Find root images (external base, not from our registry)"
    )
    parser.add_argument(
        "--src",
        default="src",
        help="Source directory containing image subdirectories (default: src)"
    )

    args = parser.parse_args()

    if args.roots:
        result = find_roots(args.src)
    else:
        result = find_dependents(args.from_image, args.src)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
