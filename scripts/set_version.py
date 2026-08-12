#!/usr/bin/env python3
"""Update all repository-owned version sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    """Replace one version expression in a text file."""
    text = path.read_text()
    updated, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"Could not update version in {path}")
    path.write_text(updated)


def update_manifest(version: str) -> None:
    """Update the Home Assistant manifest version."""
    path = ROOT / "custom_components/ai_usage/manifest.json"
    data = json.loads(path.read_text())
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    """Update manifest, Python integration version, package metadata, and badge."""
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    version = parser.parse_args().version

    update_manifest(version)
    replace_once(
        ROOT / "custom_components/ai_usage/const.py",
        r'INTEGRATION_VERSION = "[^"]+"',
        f'INTEGRATION_VERSION = "{version}"',
    )
    replace_once(
        ROOT / "pyproject.toml",
        r'(?m)^version = "[^"]+"$',
        f'version = "{version}"',
    )
    replace_once(
        ROOT / "README.md",
        r'(alt="Version" src="https://img\.shields\.io/badge/Version-)[^?]+',
        rf'\g<1>{version}',
    )


if __name__ == "__main__":
    main()
