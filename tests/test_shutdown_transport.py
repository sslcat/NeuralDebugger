import json

import httpx
import pytest

from ops.watchdog import Provider, terminate, trip


def test_rehearsal_deadline():
    pod = {
        "gpu": {"id": "NVIDIA A40", "count": 1},
        "cloud": "SECURE",
        "cost": 0.59,
        "disk": 30,
        "status": "RUNNING",
        "actions": ["terminate"],
    }
    assert trip(pod, 299, 0, None, "rehearsal") is None
    assert trip(pod, 300, 0, None, "rehearsal") == "deadline"


@pytest.mark.parametrize("delete_status", [204, 403])
def test_provider_deletion_and_readback(tmp_path, monkeypatch, delete_status):
    monkeypatch.setenv("RUNPOD_API_KEY", "unit-test-only")
    receipt = {
        "name": "neuraldebugger-fixture",
        "id": "owned",
        "storage": {"networkVolumes": [], "globalVolumes": []},
    }
    requests = []
    deleted = False

    def handle(request):
        nonlocal deleted
        path = request.url.path
        requests.append((request.method, path))
        if path == "/v2/pods/owned":
            if request.method == "DELETE":
                deleted = delete_status == 204
                return httpx.Response(delete_status)
            if deleted:
                return httpx.Response(404)
            return httpx.Response(
                200, json={"name": receipt["name"], "id": "owned", "status": "RUNNING"}
            )
        field = {
            "/v2/network-volumes": "networkVolumes",
            "/v2/global-volumes": "globalVolumes",
        }[path]
        return httpx.Response(
            200, json={field: [], "pagination": {"hasNextPage": False}}
        )

    api = Provider()
    api.http.close()
    with httpx.Client(
        base_url="https://fixture.invalid/v2", transport=httpx.MockTransport(handle)
    ) as api.http:
        if delete_status == 403:
            with pytest.raises(httpx.HTTPStatusError):
                terminate(api, tmp_path, receipt)
            assert not (tmp_path / "closed").exists()
        else:
            terminate(api, tmp_path, receipt)
            assert (tmp_path / "closed").exists()
            assert requests[:3] == [
                ("GET", "/v2/pods/owned"),
                ("DELETE", "/v2/pods/owned"),
                ("GET", "/v2/pods/owned"),
            ]
            assert (
                json.loads((tmp_path / "events.jsonl").read_text().splitlines()[-1])[
                    "event"
                ]
                == "termination_verified"
            )
