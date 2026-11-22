import asyncio
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from neuraldebugger.app import app, worker
from neuraldebugger.schema import Request


def test_status_page_and_validation():
    with TestClient(app) as client:
        assert "Debug a failure" in client.get("/").text
        assert client.get("/api/status").json()["mode"] == "unloaded"
        for payload in (
            {},
            {"code": "  ", "traceback": "a"},
            {"code": "a" * 12001, "traceback": "b"},
        ):
            assert client.post("/api/analyze", json=payload).status_code == 422


def test_api_propagates_inference_errors(monkeypatch):
    monkeypatch.setattr(
        worker,
        "exchange",
        AsyncMock(return_value={"error": "invalid output", "status": 502}),
    )
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/analyze", json={"code": "a", "traceback": "b"}
            ).status_code
            == 502
        )


def test_timeout_releases_worker(monkeypatch):
    async def stalled(_):
        await asyncio.sleep(5)

    monkeypatch.setattr(worker, "exchange", stalled)
    monkeypatch.setenv("ND_TIMEOUT", "0.01")
    with TestClient(app) as client:
        r = client.post("/api/analyze", json={"code": "a", "traceback": "b"})
        assert r.status_code == 504
        assert not worker.lock.locked()


def test_busy_worker_returns_429():
    async def check():
        async with worker.lock:
            try:
                await worker.analyze(Request(code="pass", traceback="error"))
            except Exception as exc:
                assert exc.status_code == 429
            else:
                raise AssertionError("Concurrent job admitted")

    asyncio.run(check())
