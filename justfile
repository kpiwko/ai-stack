default:
    @just --list

# Start all compose services
up:
    podman compose up -d

# Stop all compose services
down:
    podman compose down

# Show compose service status
status:
    podman compose ps
