"""Run on an independent, supervised host. This module cannot create a pod."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.parse import quote

import httpx

API = "https://api.runpod.io/v2"
MAX_SECONDS = 5400
MAX_RATE = 0.59
STORAGE_RATE = 30 * 0.10 / (28 * 24)
COST_TRIP = 0.90
STALL_SECONDS = 360


class Provider:
    def __init__(self):
        self.http = httpx.Client(
            base_url=API,
            headers={"Authorization": "Bearer " + os.environ["RUNPOD_API_KEY"]},
            timeout=8,
            follow_redirects=False,
            trust_env=False,
        )

    def pages(self, path, key):
        items, seen, params = [], set(), {}
        while True:
            r = self.http.get(path, params=params)
            r.raise_for_status()
            data = r.json()
            items.extend(data[key])
            if not data["pagination"]["hasNextPage"]:
                return items
            cursor = data["pagination"]["nextCursor"]
            if not cursor or cursor in seen:
                raise ValueError("Invalid provider pagination")
            seen.add(cursor)
            params = {"cursor": cursor}

    def storage(self):
        return {
            key: sorted(str(v["id"]) for v in self.pages(path, key))
            for path, key in (
                ("/network-volumes", "networkVolumes"),
                ("/global-volumes", "globalVolumes"),
            )
        }

    def find(self, receipt):
        matches = [
            p for p in self.pages("/pods", "pods") if p["name"] == receipt["name"]
        ]
        if len(matches) > 1:
            raise ValueError("Multiple pods match the deployment receipt")
        if matches and receipt.get("id") not in (None, matches[0]["id"]):
            raise ValueError("Pod identity changed")
        return matches[0] if matches else None

    def delete(self, pod_id):
        response = self.http.delete("/pods/" + quote(pod_id, safe=""))
        if response.status_code not in (204, 404):
            response.raise_for_status()
        return response.status_code

    def by_id(self, pod_id):
        r = self.http.get("/pods/" + quote(pod_id, safe=""))
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def gone(self, pod_id):
        pod = self.by_id(pod_id)
        return pod is None or pod["status"] == "TERMINATED"


def persist(folder, receipt):
    temp = folder / "receipt.tmp"
    temp.write_text(json.dumps(receipt, indent=2))
    temp.replace(folder / "receipt.json")


def event(folder, name, **fields):
    line = json.dumps(
        dict(time=datetime.now(timezone.utc).isoformat(), event=name, **fields)
    )
    with (folder / "events.jsonl").open("a") as f:
        f.write(line + "\n")
    print(line, file=sys.stderr, flush=True)
    if "unconfirmed" in name:
        (folder / "ALERT.txt").write_text(line)


def terminate(api, folder, receipt):
    pod = api.by_id(receipt["id"]) if receipt.get("id") else api.find(receipt)
    if pod and (
        pod["name"] != receipt["name"] or receipt.get("id", pod["id"]) != pod["id"]
    ):
        raise ValueError("Provider identity mismatch during cleanup")
    if pod and pod["status"] != "TERMINATED":
        receipt["id"] = pod["id"]
        persist(folder, receipt)
        code = api.delete(pod["id"])
        event(folder, "terminate_attempt", id=pod["id"], http_status=code)
    if not receipt.get("id") or not api.gone(receipt["id"]):
        raise RuntimeError("Termination unconfirmed")
    current = api.storage()
    delta = {
        key: sorted(set(current[key]) - set(old))
        for key, old in receipt["storage"].items()
    }
    if any(delta.values()):
        event(folder, "storage_unconfirmed", new_volume_ids=delta)
        raise RuntimeError("New storage requires attribution")
    event(folder, "termination_verified", id=receipt["id"], storage_delta=delta)
    (folder / "closed").touch()


def trip(pod, elapsed, age, signal, phase="training"):
    rate = float(pod["cost"])
    if rate < 0 or rate > MAX_RATE or not rate:
        return "unapproved hourly quote"
    if pod.get("gpu", {}).get("id") != "NVIDIA A40" or pod["gpu"].get("count") != 1:
        return "configuration mismatch"
    if pod.get("cloud") != "SECURE":
        return "cloud mismatch"
    if (
        int(pod["disk"]) > 30
        or pod.get("mounts")
        or pod.get("locked")
        or "terminate" not in pod.get("actions", [])
    ):
        return "storage or shutdown mismatch"
    limit_seconds, limit_cost = (
        (300, 0.05) if phase == "rehearsal" else (MAX_SECONDS, COST_TRIP)
    )
    if elapsed >= limit_seconds or elapsed * (rate + STORAGE_RATE) / 3600 >= limit_cost:
        return "deadline"
    if age > STALL_SECONDS or pod.get("status") in {"EXITED", "ERROR", "TERMINATED"}:
        return "stalled or stopped"
    return signal


def watch(api, folder, receipt, emergency=False):
    stopping = emergency
    started = time.monotonic()
    next_log = 0.0
    while True:
        try:
            if stopping and receipt.get("id"):
                terminate(api, folder, receipt)
                return
            pod = api.find(receipt)
            now = time.time()
            if pod:
                created = datetime.fromisoformat(
                    pod["createdAt"].replace("Z", "+00:00")
                ).timestamp()
                receipt.update(id=pod["id"], created_at=created)
                persist(folder, receipt)
                marker = folder / "progress"
                stamp = (
                    marker.stat().st_mtime if marker.exists() else receipt["armed_at"]
                )
                signal = next(
                    (
                        s
                        for s in ("abort", "failed", "recovered")
                        if (folder / s).exists()
                    ),
                    None,
                )
                elapsed = max(
                    time.monotonic() - started, now - min(created, receipt["armed_at"])
                )
                reason = trip(
                    pod, elapsed, now - stamp, signal, receipt.get("phase", "training")
                )
                if elapsed >= next_log:
                    event(
                        folder,
                        "monitor",
                        elapsed_seconds=elapsed,
                        estimated_usd=elapsed
                        * (float(pod["cost"]) + STORAGE_RATE)
                        / 3600,
                    )
                    next_log = elapsed + 60
                if reason:
                    event(folder, "shutdown_trigger", reason=reason)
                    stopping = True
            elif receipt.get("id"):
                stopping = True
            elif now - receipt["armed_at"] >= STALL_SECONDS:
                # A create request may have timed out client-side. Keep watching for late arrival.
                stopping = True
                event(folder, "creation_unconfirmed")
            if stopping and (pod or receipt.get("id")):
                terminate(api, folder, receipt)
                return
        except KeyboardInterrupt:
            stopping = True
            event(folder, "interrupt_shutdown_requested")
        except (httpx.HTTPError, KeyError, ValueError, RuntimeError, OSError) as exc:
            stopping = True
            response = getattr(exc, "response", None)
            event(
                folder,
                "shutdown_unconfirmed",
                error=type(exc).__name__,
                http_status=getattr(response, "status_code", None),
            )
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            stopping = True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["arm", "resume", "emergency"])
    p.add_argument("folder", type=Path)
    p.add_argument("--phase", choices=["training", "rehearsal"], default="training")
    args = p.parse_args()
    api = Provider()
    if args.action == "arm":
        storage = api.storage()
        api.pages("/pods", "pods")
        args.folder.mkdir(parents=True, exist_ok=False)
        receipt = dict(
            name="neuraldebugger-" + secrets.token_hex(10),
            armed_at=time.time(),
            phase=args.phase,
            storage=storage,
        )
        persist(args.folder, receipt)
        event(args.folder, "armed", name_tag=receipt["name"])
    else:
        receipt = json.loads((args.folder / "receipt.json").read_text())
    watch(api, args.folder, receipt, args.action == "emergency")


if __name__ == "__main__":
    main()
