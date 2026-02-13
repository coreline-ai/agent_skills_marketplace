#!/usr/bin/env python3
"""Monitor API/Web health endpoints and write JSONL records."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Health monitor for 24h post-deploy validation.")
    parser.add_argument("--api-url", default="http://localhost:8000/health")
    parser.add_argument("--web-url", default="http://localhost:3004/health")
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--duration-minutes", type=int, default=1440)
    parser.add_argument("--output", default="ops/monitor/health-monitor.jsonl")
    return parser.parse_args()


def check_url(url: str, timeout: int = 10) -> tuple[int, str]:
    try:
        with request.urlopen(url, timeout=timeout) as resp:  # nosec B310 (controlled URLs/monitoring)
            status = int(getattr(resp, "status", 0) or 0)
            body = resp.read(400).decode("utf-8", errors="replace")
            return status, body
    except error.HTTPError as exc:  # pragma: no cover
        return int(exc.code or 0), str(exc)
    except Exception as exc:  # pragma: no cover
        return 0, str(exc)


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    total_checks = max(1, int((args.duration_minutes * 60) / max(1, args.interval_seconds)))
    start = datetime.now(timezone.utc).isoformat()
    print(f"[monitor] start={start}")
    print(f"[monitor] api={args.api_url} web={args.web_url}")
    print(f"[monitor] interval={args.interval_seconds}s duration={args.duration_minutes}m checks={total_checks}")
    print(f"[monitor] output={output}")

    failures = 0
    with output.open("a", encoding="utf-8") as f:
        for i in range(total_checks):
            ts = datetime.now(timezone.utc).isoformat()
            api_status, api_body = check_url(args.api_url)
            web_status, web_body = check_url(args.web_url)
            ok = api_status == 200 and web_status == 200
            if not ok:
                failures += 1

            record = {
                "timestamp": ts,
                "api_status": api_status,
                "web_status": web_status,
                "ok": ok,
                "api_body_sample": api_body,
                "web_body_sample": web_body,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            if i < total_checks - 1:
                time.sleep(max(1, args.interval_seconds))

    end = datetime.now(timezone.utc).isoformat()
    print(f"[monitor] end={end} failures={failures}/{total_checks}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
