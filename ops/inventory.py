"""Capture public Runpod on-demand quotes. Does not access an account."""

import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

QUERY = """{ gpuTypes { id memoryInGb
 secure: lowestPrice(input:{gpuCount:1,secureCloud:true}) { stockStatus uninterruptablePrice }
 community: lowestPrice(input:{gpuCount:1,secureCloud:false}) { stockStatus uninterruptablePrice }
} }"""


def snapshot():
    url = "https://api.runpod.io/graphql"
    r = httpx.post(url, json={"query": QUERY}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(data["errors"][0]["message"])
    offers = []
    for gpu in data["data"]["gpuTypes"]:
        for lane in ("secure", "community"):
            q = gpu.get(lane) or {}
            if (
                gpu["memoryInGb"] >= 8
                and q.get("uninterruptablePrice")
                and q.get("stockStatus", "").lower() in {"low", "medium", "high"}
            ):
                offers.append(
                    dict(
                        gpu=gpu["id"],
                        gb=gpu["memoryInGb"],
                        cloud=lane,
                        usd_per_hour=q["uninterruptablePrice"],
                        stock=q["stockStatus"],
                    )
                )
    return dict(
        utc=datetime.now(timezone.utc).isoformat(),
        source=url,
        query=QUERY,
        offers=sorted(offers, key=lambda x: x["usd_per_hour"]),
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = snapshot()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as f:
        json.dump(data, f, indent=2)
    print(data["utc"], data["offers"][:5])
