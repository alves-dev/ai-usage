#!/usr/bin/env python3
"""Generate and optionally send a manual AI Usage payload 2.0."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
import sys
from urllib.request import Request, urlopen

MAX_PERCENT = 100
COLLECTOR_VERSION = "2026.8.0"


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    """Build a valid normalized two-window payload."""
    now = datetime.now(UTC).replace(microsecond=0)
    short_reset = now + timedelta(hours=5)
    weekly_reset = now + timedelta(days=7)
    return {
        "schema_version": "2.0",
        "collected_at": now.isoformat().replace("+00:00", "Z"),
        "provider": args.provider,
        "status": "ok",
        "collector_data": {
            "id": "manual_test",
            "version": COLLECTOR_VERSION,
            "transport": "webhook",
        },
        "account_data": {
            "id": args.account_id,
            "id_kind": "provider_account_id",
            "label": args.account_label,
            "username": args.account_label,
            "plan": {"type": args.plan},
        },
        "usage_data": {
            "windows": [
                {
                    "id": "short",
                    "label": args.short_label,
                    "duration_seconds": 18000,
                    "used_percent": args.short_used,
                    "reset_at": short_reset.isoformat().replace("+00:00", "Z"),
                    "limit_reached": args.short_used >= MAX_PERCENT,
                },
                {
                    "id": "long",
                    "label": args.long_label,
                    "duration_seconds": 604800,
                    "used_percent": args.long_used,
                    "reset_at": weekly_reset.isoformat().replace("+00:00", "Z"),
                    "limit_reached": args.long_used >= MAX_PERCENT,
                },
            ]
        },
        "error": None,
    }


def send_payload(url: str, payload: dict[str, object]) -> None:
    """POST a payload to a Home Assistant webhook URL."""
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        response_body = response.read().decode("utf-8")
        sys.stdout.write(f"HTTP {response.status}\n{response_body}\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Generate or send an AI Usage payload 2.0."
    )
    parser.add_argument(
        "--url",
        help="Webhook URL. If omitted, the payload is only printed.",
    )
    parser.add_argument("--provider", default="codex")
    parser.add_argument("--account-id", default="manual-account-001")
    parser.add_argument("--account-label", default="Manual test account")
    parser.add_argument("--plan", default="plus")
    parser.add_argument("--short-used", type=float, default=25.0)
    parser.add_argument("--long-used", type=float, default=42.0)
    parser.add_argument("--short-label", default="5-hour window")
    parser.add_argument("--long-label", default="Weekly window")
    return parser.parse_args()


def main() -> None:
    """Generate and optionally send the payload."""
    args = parse_args()
    for name in ("short_used", "long_used"):
        value = getattr(args, name)
        if not 0 <= value <= MAX_PERCENT:
            raise SystemExit(f"--{name.replace('_', '-')} must be between 0 and 100")

    payload = build_payload(args)
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    if args.url:
        send_payload(args.url, payload)


if __name__ == "__main__":
    main()
