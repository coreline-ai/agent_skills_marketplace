#!/usr/bin/env python3
"""Verify 24h health monitoring result file."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a 24h health monitor JSONL result.")
    parser.add_argument("--input", required=True, help="Path to monitoring JSONL file.")
    parser.add_argument("--min-hours", type=float, default=24.0)
    return parser.parse_args()


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[verify] file not found: {input_path}")
        return 2

    rows = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if not rows:
        print("[verify] no samples")
        return 1

    start = parse_ts(rows[0]["timestamp"])
    end = parse_ts(rows[-1]["timestamp"])
    elapsed_hours = (end - start).total_seconds() / 3600.0
    failures = sum(1 for r in rows if not r.get("ok"))

    print(f"[verify] samples={len(rows)} failures={failures}")
    print(f"[verify] start={rows[0]['timestamp']} end={rows[-1]['timestamp']}")
    print(f"[verify] elapsed_hours={elapsed_hours:.2f} (required>={args.min_hours:.2f})")

    if failures > 0:
        print("[verify] fail: failures detected")
        return 1
    if elapsed_hours < float(args.min_hours):
        print("[verify] fail: monitoring window not completed")
        return 1

    print("[verify] pass: 24h monitoring healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
