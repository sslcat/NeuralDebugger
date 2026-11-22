"""Exercise each real inference mode on localhost, one GPU worker at a time."""

import json
import os
import socket
import subprocess
import sys
import threading
import time

import httpx
import uvicorn

from neuraldebugger.data import load
from neuraldebugger.hybrid_trial import ADAPTER, OUT


def check(mode, *, missing=False):
    checkpoint = ADAPTER / ("missing-checkpoint" if missing else "epoch-3")
    os.environ.update(
        ND_DEVICE="cuda", ND_BACKEND=mode, HF_HUB_OFFLINE="1", ND_ADAPTER=str(checkpoint)
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
                subprocess.run(
                    [sys.executable, "-m", "tools.browser_check", "--url", url,
                     "--analyze", "--expect", mode],
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
            return httpx.get(url + "/api/status").json()
        finally:
            server.should_exit = True
            thread.join(30)
            if thread.is_alive():
                raise RuntimeError("Browser-test worker shutdown unconfirmed")


def main():
    modes = ("base", "adapter", "hybrid-display", "hybrid-conditioned")
    evidence = {mode: check(mode) for mode in modes}
    evidence["missing-adapter"] = check("hybrid-conditioned", missing=True)
    with (OUT / "browser-checks.json").open("x", encoding="utf8") as f:
        json.dump(evidence, f, indent=2)
    print("Four real browser configurations, truthiness check and missing-adapter fallback passed")


if __name__ == "__main__":
    main()
