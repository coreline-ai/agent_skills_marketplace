#!/usr/bin/env python3
"""Measure search latency and ordering stability for quality gates."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ModeResult:
    mode: str
    total_runs: int
    p50_ms: float
    p95_ms: float
    avg_ms: float
    stability_exact_ratio: float
    baseline_top_ids: list[str]


def percentile(values: list[float], p: float) -> float:
    """Return percentile with linear interpolation."""
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return sorted_values[lower]
    weight = index - lower
    return (sorted_values[lower] * (1.0 - weight)) + (sorted_values[upper] * weight)


def extract_top_ids(payload: dict[str, Any], top_n: int) -> list[str]:
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    return [str(item.get("id")) for item in items[:top_n] if isinstance(item, dict) and item.get("id")]


def run_mode(
    *,
    session: requests.Session,
    base_url: str,
    mode: str,
    query: str,
    runs: int,
    top_n: int,
    size: int,
    warmup: int,
    timeout: float,
) -> ModeResult:
    latencies: list[float] = []
    baseline_top_ids: list[str] = []
    exact_match_count = 0

    for index in range(runs + warmup):
        started = time.perf_counter()
        response = session.get(
            f"{base_url.rstrip('/')}/skills",
            params={"q": query, "mode": mode, "size": size, "page": 1},
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        if response.status_code != 200:
            raise RuntimeError(
                f"Request failed mode={mode} status={response.status_code} body={response.text[:300]}"
            )

        if index < warmup:
            continue

        latencies.append(elapsed_ms)
        payload = response.json()
        top_ids = extract_top_ids(payload, top_n)
        if not baseline_top_ids:
            baseline_top_ids = top_ids
            exact_match_count += 1
        elif top_ids == baseline_top_ids:
            exact_match_count += 1

    total_runs = len(latencies)
    return ModeResult(
        mode=mode,
        total_runs=total_runs,
        p50_ms=percentile(latencies, 0.50),
        p95_ms=percentile(latencies, 0.95),
        avg_ms=statistics.mean(latencies) if latencies else 0.0,
        stability_exact_ratio=(exact_match_count / total_runs) if total_runs else 0.0,
        baseline_top_ids=baseline_top_ids,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark /api/skills search latency and ordering stability."
    )
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--query", default="coding")
    parser.add_argument("--modes", default="keyword,vector,hybrid")
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json", action="store_true", help="Print JSON output only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if not modes:
        raise SystemExit("At least one mode is required.")
    if args.runs <= 0:
        raise SystemExit("--runs must be > 0")

    results: list[ModeResult] = []
    with requests.Session() as session:
        for mode in modes:
            results.append(
                run_mode(
                    session=session,
                    base_url=args.base_url,
                    mode=mode,
                    query=args.query,
                    runs=args.runs,
                    top_n=args.top_n,
                    size=args.size,
                    warmup=args.warmup,
                    timeout=args.timeout,
                )
            )

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "mode": item.mode,
                        "total_runs": item.total_runs,
                        "p50_ms": round(item.p50_ms, 2),
                        "p95_ms": round(item.p95_ms, 2),
                        "avg_ms": round(item.avg_ms, 2),
                        "stability_exact_ratio": round(item.stability_exact_ratio, 4),
                        "baseline_top_ids": item.baseline_top_ids,
                    }
                    for item in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print("Search Benchmark Result")
    print(f"- base_url: {args.base_url}")
    print(f"- query: {args.query}")
    print(f"- runs: {args.runs} (warmup: {args.warmup})")
    print(f"- top_n: {args.top_n}")
    print("")
    for item in results:
        print(f"[{item.mode}]")
        print(f"  p50_ms: {item.p50_ms:.2f}")
        print(f"  p95_ms: {item.p95_ms:.2f}")
        print(f"  avg_ms: {item.avg_ms:.2f}")
        print(f"  stability_exact_ratio: {item.stability_exact_ratio:.4f}")
        if item.baseline_top_ids:
            print(f"  baseline_top_ids: {', '.join(item.baseline_top_ids[:5])}")
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
