"""Exercise each real inference mode on localhost, one GPU worker at a time."""

import argparse
import json
from pathlib import Path
import os
import socket
import subprocess
import sys
import threading
import time

import httpx
import uvicorn

from neuraldebugger.data import load
from neuraldebugger.settings import ROOT


def check(mode, *, missing=False, device='cuda', screenshots=None, adapter=None):
    checkpoint = Path(adapter or ROOT / "adapters/epoch-3")
    if missing:
        checkpoint = checkpoint.parent / "missing-checkpoint"
    os.environ.update(
        ND_DEVICE=device, ND_BACKEND=mode, HF_HUB_OFFLINE="1", ND_ADAPTER=str(checkpoint)
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        server = uvicorn.Server(uvicorn.Config("neuraldebugger.app:app", log_level="warning"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 20
            while not server.started:
                if not thread.is_alive() or time.monotonic() >= deadline:
                    raise RuntimeError("Local browser test server failed to start")
                time.sleep(0.1)
            if not missing:
                capture = ["--shot-dir", str(screenshots / mode)] if screenshots else []
                subprocess.run(
                    [sys.executable, "-m", "tools.browser_check", "--url", url,
                     "--analyze", "--expect", mode, *capture],
                    check=True, timeout=200,
                )
            if mode == "hybrid-display" or missing:
                case = next(r for r in load("test") if r["id"] == "predicate-call")
                response = httpx.post(
                    url + "/api/analyze", timeout=160,
                    json={"code": case["buggy_code"], "traceback": case["traceback"]},
                )
                response.raise_for_status()
                data = response.json()
                assert data["prose_source"] == "Python semantics check"
                assert "empty result is false" in data["diagnosis"]["explanation"]
                if missing:
                    assert data["mode"] == "base" and data["warning"] and "hybrid" not in data
            status = httpx.get(url + "/api/status").json()
            assert status["device"] == device and status["mode"] == ("base" if missing else mode)
            return status
        finally:
            server.should_exit = True
            thread.join(30)
            if thread.is_alive():
                raise RuntimeError("Browser-test worker shutdown unconfirmed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true", help="Test base inference on CPU only")
    parser.add_argument("--out", type=Path, default=ROOT / ".runs/browser-checks.json")
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    modes = ("base",) if args.cpu else ("base", "adapter", "hybrid-display", "hybrid-conditioned")
    device = "cpu" if args.cpu else "cuda"
    evidence = {m: check(m, device=device, screenshots=args.screenshots) for m in modes}
    if not args.cpu:
        evidence["missing-adapter"] = check("hybrid-conditioned", missing=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf8") as f:
        json.dump(evidence, f, indent=2)
    print("Verified live modes:", ", ".join(evidence), "on", device)


if __name__ == "__main__":
    main()
