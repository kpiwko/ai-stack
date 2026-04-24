default:
    @just --list

# Print Claude Code /plugin install commands (run them inside Claude Code)
install-plugins:
    #!/usr/bin/env bash
    set -euo pipefail
    count=$(yq '.plugins | length' plugins.yaml)
    if [ "$count" -eq 0 ]; then
        echo "No plugins configured in plugins.yaml"
        exit 0
    fi
    echo "Run these inside Claude Code:"
    for i in $(seq 0 $((count - 1))); do
        name=$(yq ".plugins[$i].name" plugins.yaml)
        source=$(yq ".plugins[$i].source" plugins.yaml)
        echo "  /plugin install ${name}@${source}"
    done

# Install bare skills from 3rd party repos (requires: yq, git)
install-skills:
    #!/usr/bin/env bash
    set -euo pipefail
    count=$(yq '.skills | length' plugins.yaml)
    if [ "$count" -eq 0 ]; then
        echo "No skills configured in plugins.yaml"
        exit 0
    fi
    for i in $(seq 0 $((count - 1))); do
        name=$(yq ".skills[$i].name" plugins.yaml)
        source=$(yq ".skills[$i].source" plugins.yaml)
        path=$(yq ".skills[$i].path // \"\"" plugins.yaml)
        version=$(yq ".skills[$i].version // \"main\"" plugins.yaml)
        scope=$(yq ".skills[$i].scope // \"project\"" plugins.yaml)

        if [ "$scope" = "global" ]; then
            target="$HOME/.claude/skills/$name"
        else
            target=".claude/skills/$name"
        fi

        echo "Installing $name → $target"
        tmpdir=$(mktemp -d)
        trap "rm -rf $tmpdir" EXIT

        git clone --depth 1 --filter=blob:none --sparse --branch "$version" \
            "https://github.com/$source" "$tmpdir" 2>/dev/null

        if [ -n "$path" ]; then
            git -C "$tmpdir" sparse-checkout set "$path" 2>/dev/null
            mkdir -p "$target"
            cp -r "$tmpdir/$path/." "$target/"
        else
            mkdir -p "$target"
            cp -r "$tmpdir/." "$target/"
        fi

        trap - EXIT
        rm -rf "$tmpdir"
        echo "  ✓ done"
    done

# Check compose services all use ghcr.io images (not localhost/)
check-images:
    @grep -n 'image: localhost/' compose.yaml && echo "FAIL: localhost/ images found" && exit 1 || echo "OK: all images use remote registry"

# Start all compose services
up:
    podman compose up -d

# Stop all compose services
down:
    podman compose down

# Show compose service status
status:
    podman compose ps
