from types import SimpleNamespace
from typing import Any

import main as entrypoint


def test_main_disables_uvicorn_access_log(monkeypatch: Any) -> None:
    uvicorn_call: dict[str, Any] = {}

    def fake_run(app_path: str, **kwargs: Any) -> None:
        uvicorn_call["app_path"] = app_path
        uvicorn_call.update(kwargs)

    monkeypatch.setattr(
        entrypoint,
        "get_settings",
        lambda: SimpleNamespace(host="127.0.0.1", port=5050),
    )
    monkeypatch.setattr(entrypoint, "log_info", lambda _message: None)
    monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)

    entrypoint.main()

    assert uvicorn_call["app_path"] == "app.main:app"
    assert uvicorn_call["host"] == "127.0.0.1"
    assert uvicorn_call["port"] == 5050
    assert uvicorn_call["access_log"] is False
    assert uvicorn_call["log_config"] is None
