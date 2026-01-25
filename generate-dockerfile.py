#!/usr/bin/env python3
"""
Generate Dockerfile from tools.yaml configuration.

Supports multiple base images (Alpine, Debian, actions-runner) and
package managers (apk, apt).
"""

import argparse
import sys
from pathlib import Path


def parse_yaml_simple(content: str) -> dict:
    """Simple YAML parser for our specific format."""
    result = {}
    current_list = None
    current_list_key = None
    current_item = None
    current_key = None
    multiline_value = []
    in_multiline = False
    multiline_indent = 0

    lines = content.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            if in_multiline and line and not stripped.startswith('#'):
                multiline_value.append('')
            continue

        indent = len(line) - len(line.lstrip())

        # Handle multiline values
        if in_multiline:
            if indent > multiline_indent or (indent == multiline_indent and not stripped.startswith('-')):
                multiline_value.append(stripped)
                continue
            else:
                if current_item and current_key:
                    current_item[current_key] = '\n'.join(multiline_value)
                elif current_key:
                    result[current_key] = '\n'.join(multiline_value)
                in_multiline = False
                multiline_value = []

        # List item
        if stripped.startswith('- '):
            if current_list_key and ':' in stripped:
                # New item in list with key-value
                if current_item:
                    current_list.append(current_item)
                key_val = stripped[2:].split(':', 1)
                current_item = {key_val[0].strip(): key_val[1].strip()}
            elif current_list_key:
                # Simple list item
                current_list.append(stripped[2:])
            continue

        # Key-value pair
        if ':' in stripped and not stripped.startswith('-'):
            key, value = stripped.split(':', 1)
            key = key.strip()
            value = value.strip()
            # Strip YAML outer quotes
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]

            # Check if this is starting a list
            if value == '' and indent == 0:
                if current_list_key and current_list is not None:
                    if current_item:
                        current_list.append(current_item)
                        current_item = None
                    result[current_list_key] = current_list
                current_list_key = key
                current_list = []
                current_item = None
                continue

            if value == '|':
                in_multiline = True
                multiline_indent = indent
                current_key = key
                multiline_value = []
            elif current_item is not None:
                current_item[key] = value
            else:
                result[key] = value

    # Finalize
    if in_multiline and current_key:
        if current_item:
            current_item[current_key] = '\n'.join(multiline_value)
        else:
            result[current_key] = '\n'.join(multiline_value)

    if current_list_key and current_list is not None:
        if current_item:
            current_list.append(current_item)
        result[current_list_key] = current_list

    return result


def generate_dockerfile(config: dict, image_name: str) -> str:
    """Generate Dockerfile content from tools configuration."""

    base = config.get('base', 'alpine:3.22')
    multi_arch = config.get('multi_arch', 'false').lower() == 'true'
    pkg_manager = config.get('package_manager', 'apk')
    tools = config.get('tools', [])
    workdir = config.get('workdir', '/app')
    user = config.get('user', '')
    entrypoint = config.get('entrypoint', '')
    build_args = config.get('build_args', [])

    lines = [
        f"# {image_name} Image",
        "# AUTO-GENERATED from tools.yaml - do not edit directly!",
        "#",
        "# Tools included:",
    ]

    for tool in tools:
        if isinstance(tool, dict):
            name = tool.get('name', 'unknown')
            desc = tool.get('description', name)
            lines.append(f"#   - {name}: {desc}")

    lines.append("")

    # Base image
    if multi_arch:
        lines.append(f"FROM --platform=$TARGETPLATFORM {base}")
        lines.append("ARG TARGETPLATFORM")
        lines.append("ARG BUILDPLATFORM")
        lines.append("")
    else:
        lines.append(f"FROM {base}")
        lines.append("")

    # Labels
    lines.extend([
        'LABEL org.opencontainers.image.authors="tompisula@labrats.work"',
        'LABEL org.opencontainers.image.source="https://github.com/labrats-work/infra.images"',
        f'LABEL org.opencontainers.image.description="{image_name} infrastructure image"',
        "",
    ])

    # Build args
    for arg in build_args:
        if isinstance(arg, dict):
            name = arg.get('name', '')
            default = arg.get('default', '')
            lines.append(f"ARG {name}={default}")
            lines.append(f"ENV {name}=${{{name}}}")
    if build_args:
        lines.append("")

    # Switch to root if needed
    if user:
        lines.append("USER root")
        lines.append("")

    # Group tools by method
    pkg_tools = []
    binary_tools = []
    script_tools = []

    for tool in tools:
        if isinstance(tool, dict):
            method = tool.get('method', 'package')
            if method == 'package':
                pkg_tools.append(tool)
            elif method == 'binary':
                binary_tools.append(tool)
            elif method == 'script':
                script_tools.append(tool)

    # Install packages
    if pkg_tools:
        packages = ' '.join(t.get('package', t.get('name', '')) for t in pkg_tools)
        if pkg_manager == 'apk':
            lines.extend([
                "# Install packages",
                f"RUN apk add --no-cache {packages}",
                "",
            ])
        elif pkg_manager == 'apt':
            lines.extend([
                "# Install packages",
                "RUN apt-get update && \\",
                f"    apt-get install -y --no-install-recommends {packages} && \\",
                "    rm -rf /var/lib/apt/lists/*",
                "",
            ])

    # Install binaries
    for tool in binary_tools:
        name = tool.get('name', '')
        desc = tool.get('description', name)
        url = tool.get('url', '')
        dest = tool.get('dest', f'/usr/local/bin/{name}')
        arch_script = tool.get('arch_script', '')

        lines.append(f"# Install {name} ({desc})")
        if arch_script:
            lines.append(f"RUN {arch_script}")
        else:
            lines.extend([
                f'RUN curl -fsSL "{url}" -o {dest} && \\',
                f"    chmod +x {dest}",
            ])
        lines.append("")

    # Run scripts
    for tool in script_tools:
        name = tool.get('name', '')
        desc = tool.get('description', name)
        script = tool.get('script', '').strip()

        lines.append(f"# Install {name} ({desc})")
        script_lines = [cmd.strip() for cmd in script.split('\n') if cmd.strip()]
        lines.append("RUN " + " && \\\n    ".join(script_lines))
        lines.append("")

    # Workdir
    if workdir:
        lines.append(f"WORKDIR {workdir}")
        lines.append("")

    # Switch back to user
    if user:
        lines.append(f"USER {user}")
        lines.append("")

    # Entrypoint
    if entrypoint:
        lines.append(f"ENTRYPOINT {entrypoint}")
    else:
        lines.append("ENTRYPOINT []")
    lines.append("CMD []")
    lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Dockerfile from tools.yaml configuration'
    )
    parser.add_argument(
        '--image', '-i',
        required=True,
        help='Image directory name (e.g., ansible, terraform)'
    )
    parser.add_argument(
        '--src', '-s',
        default='src',
        help='Source directory containing image subdirectories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print Dockerfile to stdout instead of writing'
    )

    args = parser.parse_args()

    image_dir = Path(args.src) / args.image
    tools_file = image_dir / 'tools.yaml'
    dockerfile = image_dir / 'dockerfile'

    if not tools_file.exists():
        print(f"Error: {tools_file} not found", file=sys.stderr)
        sys.exit(1)

    content = tools_file.read_text()

    try:
        config = parse_yaml_simple(content)
    except Exception as e:
        print(f"Error parsing {tools_file}: {e}", file=sys.stderr)
        sys.exit(1)

    dockerfile_content = generate_dockerfile(config, args.image)

    if args.dry_run:
        print(dockerfile_content)
    else:
        dockerfile.write_text(dockerfile_content)
        print(f"Generated {dockerfile}")


if __name__ == '__main__':
    main()
