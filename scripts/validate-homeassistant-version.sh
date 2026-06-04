#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HA_VERSION="${HA_VERSION:-2026.5.0}"

if [[ "${1:-}" =~ ^[0-9]{4}\.[0-9]+\.[0-9]+$ ]]; then
  HA_VERSION="$1"
  shift
fi

cd "$ROOT_DIR"

echo "Validating AI Usage with Home Assistant ${HA_VERSION}"

uv run \
  --isolated \
  --no-project \
  --python 3.14 \
  --with "homeassistant==${HA_VERSION}" \
  --with "pytest>=8.4.0" \
  --with "pytest-asyncio>=1.2.0" \
  python -m pytest -c "$ROOT_DIR/pyproject.toml" "$ROOT_DIR/tests" "$@"
