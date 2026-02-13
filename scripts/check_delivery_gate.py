#!/usr/bin/env python3
"""Deployment gate checker for DELIVERY_CHECKLIST.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


UNCHECKED_RE = re.compile(r"^\s*-\s\[\s\]\s(.+?)\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check unchecked items in delivery checklist.")
    parser.add_argument(
        "--checklist",
        default="docs/DELIVERY_CHECKLIST.md",
        help="Checklist markdown file path.",
    )
    parser.add_argument(
        "--allow-contains",
        action="append",
        default=[],
        help="Allow unchecked items that contain this text. Can be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checklist = Path(args.checklist)
    if not checklist.exists():
        print(f"[gate] checklist not found: {checklist}")
        return 2

    unchecked: list[str] = []
    with checklist.open("r", encoding="utf-8") as f:
        for line in f:
            match = UNCHECKED_RE.match(line)
            if not match:
                continue
            item = match.group(1).strip()
            if any(token in item for token in args.allow_contains):
                continue
            unchecked.append(item)

    if unchecked:
        print("[gate] blocked: unchecked checklist items found")
        for idx, item in enumerate(unchecked, start=1):
            print(f"  {idx}. {item}")
        return 1

    print("[gate] pass: no blocking unchecked items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
