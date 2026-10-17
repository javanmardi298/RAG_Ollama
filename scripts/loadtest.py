"""Stage 8: measure latency under concurrent load.  python scripts/loadtest.py --users 5 --requests 40
Defaults come from configs/project.yaml -> serving.*; the API must be running (panel: "start API").
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from support.config import RESULTS_DIR  # noqa: E402
from support.monitoring import latency_summary  # noqa: E402
from support.settings import settings  # noqa: E402

MESSAGES = ["Where is my order?", "How long do I have to return something?",
            "Wie lange dauert der Versand?", "I want to cancel my order", "Kann ich mit Klarna zahlen?"]


async def user(client, n, latencies, errors):
    for i in range(n):
        start = time.perf_counter()
        try:
            r = await client.post("/chat", json={"message": MESSAGES[i % len(MESSAGES)]}, timeout=120)
            r.raise_for_status()
            latencies.append(time.perf_counter() - start)
        except Exception:
            errors.append(1)


async def main(url, users, requests):
    latencies, errors = [], []
    async with httpx.AsyncClient(base_url=url) as client:
        start = time.perf_counter()
        await asyncio.gather(*(user(client, requests // users, latencies, errors) for _ in range(users)))
        wall = time.perf_counter() - start
    if not latencies:
        raise SystemExit(f"all {len(errors)} requests failed: is the API running at {url}?")
    out = {**latency_summary(latencies), "errors": len(errors), "throughput_rps": round(len(latencies) / wall, 2),
           "users": users, "requests": requests}
    print(out)
    (RESULTS_DIR / "stage8_loadtest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    srv = settings().serving
    p.add_argument("--url", default=f"http://localhost:{srv.port}")
    p.add_argument("--users", type=int, default=srv.loadtest_users)
    p.add_argument("--requests", type=int, default=srv.loadtest_requests)
    a = p.parse_args()
    asyncio.run(main(a.url, a.users, a.requests))
