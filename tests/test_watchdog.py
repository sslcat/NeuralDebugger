import json
from unittest.mock import Mock
import httpx
import pytest
from ops.watchdog import Provider, terminate, trip, watch


def pod(**updates):
    return dict(
        {
            "id": "owned",
            "name": "neuraldebugger-unit",
            "gpu": {"id": "NVIDIA A40", "count": 1},
            "createdAt": "2026-01-01T00:00:00Z",
            "status": "RUNNING",
            "cloud": "SECURE",
            "cost": 0.59,
            "disk": 30,
            "actions": ["terminate"],
        },
        **updates,
    )


def receipt():
    return {
        "name": "neuraldebugger-unit",
        "armed_at": 1,
        "storage": {"networkVolumes": [], "globalVolumes": []},
    }


@pytest.mark.parametrize(
    "elapsed,age,signal,expected",
    [
        (5400, 0, None, "deadline"),
        (1, 361, None, "stalled or stopped"),
        (1, 1, "recovered", "recovered"),
        (1, 1, None, None),
    ],
)
def test_limits(elapsed, age, signal, expected):
    assert trip(pod(), elapsed, age, signal) == expected


def test_refuses_new_quote_or_storage():
    assert trip(pod(cost=0.60), 0, 0, None)
    assert trip(pod(mounts={"persistent": {"size": 20}}), 0, 0, None)


def test_full_monitor_path(tmp_path):
    api = Mock()
    api.find.return_value = pod()
    api.by_id.return_value = pod()
    api.delete.return_value = 204
    api.gone.return_value = True
    api.storage.return_value = receipt()["storage"]
    watch(api, tmp_path, receipt())
    api.delete.assert_called_once_with("owned")
    assert (tmp_path / "closed").exists()
    assert json.loads((tmp_path / "receipt.json").read_text())["id"] == "owned"


def test_unconfirmed_deletion_and_storage(tmp_path):
    api = Mock()
    api.find.return_value = pod()
    api.by_id.return_value = pod()
    api.delete.return_value = 204
    api.gone.return_value = False
    with pytest.raises(RuntimeError, match="unconfirmed"):
        terminate(api, tmp_path, receipt())
    api.gone.return_value = True
    api.storage.return_value = {"networkVolumes": ["new-volume"], "globalVolumes": []}
    with pytest.raises(RuntimeError, match="attribution"):
        terminate(api, tmp_path, receipt())
    assert not (tmp_path / "closed").exists()


def test_pagination_and_identity(monkeypatch):
    monkeypatch.setenv("RUNPOD_API_KEY", "unit-test-only")
    api = Provider()

    def handle(req):
        if req.url.params.get("cursor"):
            return httpx.Response(
                200, json={"pods": [pod()], "pagination": {"hasNextPage": False}}
            )
        return httpx.Response(
            200,
            json={
                "pods": [pod(name="unrelated")],
                "pagination": {"hasNextPage": True, "nextCursor": "two"},
            },
        )

    api.http.close()
    with httpx.Client(
        base_url="https://fixture.invalid", transport=httpx.MockTransport(handle)
    ) as api.http:
        assert api.find(receipt())["id"] == "owned"
        with pytest.raises(ValueError, match="identity"):
            api.find({**receipt(), "id": "different"})
