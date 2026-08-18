#!/usr/bin/env python3
"""Small dependency-light load probe for the deterministic /api/solve/ path."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import sys
import time

import requests


def request_once(url: str, timeout: float) -> tuple[bool, float, int | None]:
    started = time.perf_counter()
    try:
        response = requests.post(
            url,
            json={"equation": "Derivative(y, x) - y = 0", "variable": "x"},
            timeout=timeout,
        )
        elapsed = time.perf_counter() - started
        return response.ok, elapsed, response.status_code
    except requests.RequestException:
        elapsed = time.perf_counter() - started
        return False, elapsed, None


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/solve/")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--min-success-rate", type=float, default=0.99)
    args = parser.parse_args()

    results = []
    wall_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(request_once, args.url, args.timeout)
            for _ in range(args.requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    wall = time.perf_counter() - wall_start
    successes = [item for item in results if item[0]]
    latencies = [item[1] for item in results]
    success_rate = len(successes) / max(len(results), 1)

    print(f"requests:      {len(results)}")
    print(f"success rate:  {success_rate:.2%}")
    print(f"wall time:     {wall:.3f}s")
    print(f"throughput:    {len(results) / max(wall, 1e-9):.2f} req/s")
    print(f"mean latency:  {statistics.fmean(latencies):.4f}s")
    print(f"p50 latency:   {percentile(latencies, 0.50):.4f}s")
    print(f"p95 latency:   {percentile(latencies, 0.95):.4f}s")
    print(f"max latency:   {max(latencies, default=0.0):.4f}s")

    if success_rate < args.min_success_rate:
        print("load probe failed: success rate below threshold", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
