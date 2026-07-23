from __future__ import annotations

import asyncio
import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

_RUNNER_MODULE_NAME = "_sejong_local_api_runner_test"
_RUNNER_PATH = Path(__file__).resolve().parents[1] / "run_local_api.py"


def _database_dsn(scheme: str, authority: str) -> str:
    return f"{scheme}://{authority}"


def _runner() -> ModuleType:
    cached = sys.modules.get(_RUNNER_MODULE_NAME)
    if cached is not None:
        return cached
    if not _RUNNER_PATH.is_file():
        pytest.fail("the dedicated local API runner is missing")
    spec = importlib.util.spec_from_file_location(_RUNNER_MODULE_NAME, _RUNNER_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("the dedicated local API runner cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_RUNNER_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def test_windows_selector_policy_is_installed_before_loading_or_running_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    events: list[str] = []
    application_factory = object()

    monkeypatch.setattr(
        runner,
        "_configure_event_loop_policy",
        lambda platform: events.append(f"policy:{platform}"),
    )

    def load_factory() -> object:
        events.append("factory")
        return application_factory

    monkeypatch.setattr(runner, "_load_required_local_app_factory", load_factory)
    monkeypatch.setattr(
        runner,
        "_run_uvicorn",
        lambda factory, port: events.append(
            f"uvicorn:{factory is application_factory}:{port}"
        ),
    )
    monkeypatch.setattr(runner.sys, "platform", "win32")

    assert runner.main([]) == 0
    assert events == ["policy:win32", "factory", "uvicorn:True:8000"]


def test_win32_selects_windows_selector_event_loop_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    selected_policy = object()
    installed: list[object] = []

    monkeypatch.setattr(
        asyncio,
        "WindowsSelectorEventLoopPolicy",
        lambda: selected_policy,
        raising=False,
    )
    monkeypatch.setattr(asyncio, "set_event_loop_policy", installed.append)

    runner._configure_event_loop_policy("win32")

    assert installed == [selected_policy]


def test_non_windows_event_loop_policy_is_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    installed: list[object] = []
    monkeypatch.setattr(asyncio, "set_event_loop_policy", installed.append)

    runner._configure_event_loop_policy("linux")

    assert installed == []


def test_uvicorn_receives_only_private_single_process_safe_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    calls: list[tuple[object, dict[str, object]]] = []
    application_factory = object()

    def fake_run(app: object, **kwargs: object) -> None:
        calls.append((app, kwargs))

    uvicorn = importlib.import_module("uvicorn")
    monkeypatch.setattr(uvicorn, "run", fake_run)

    runner._run_uvicorn(application_factory, 8123)

    assert calls == [
        (
            application_factory,
            {
                "host": "127.0.0.1",
                "port": 8123,
                "factory": True,
                "loop": "none",
                "access_log": False,
                "reload": False,
                "workers": 1,
                "ws": "none",
                "proxy_headers": False,
                "server_header": False,
                "log_level": "info",
                "log_config": None,
            },
        )
    ]


@pytest.mark.parametrize("value", ["0", "1023", "65536", "not-a-port"])
def test_port_argument_is_strictly_bounded(value: str) -> None:
    runner = _runner()

    with pytest.raises(runner._ArgumentsInvalid):
        runner._parse_args(["--port", value])


def test_only_the_bounded_port_argument_is_accepted() -> None:
    runner = _runner()

    assert runner._parse_args([]).port == 8000
    assert runner._parse_args(["--port", "1024"]).port == 1024
    assert runner._parse_args(["--port", "65535"]).port == 65535
    with pytest.raises(runner._ArgumentsInvalid):
        runner._parse_args(["--host", "0.0.0.0"])
    with pytest.raises(runner._ArgumentsInvalid):
        runner._parse_args(["--reload"])
    with pytest.raises(runner._ArgumentsInvalid):
        runner._parse_args(["--workers", "2"])


def test_existing_local_factory_and_configuration_are_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner()
    for key in tuple(os.environ):
        if key.upper().startswith("PG"):
            monkeypatch.delenv(key)
    monkeypatch.setenv(
        "DATABASE_URL",
        _database_dsn(
            "postgresql", "sejong_local_login:synthetic@127.0.0.1:54322/postgres"
        ),
    )
    monkeypatch.setenv("CONTEXT_TOKEN_SECRET", "x" * 32)

    factory = runner._load_required_local_app_factory()

    local_module = importlib.import_module("sejong_ai_api.local")
    assert factory is local_module.create_local_app

    monkeypatch.setenv("CONTEXT_TOKEN_SECRET", "short")
    with pytest.raises(runner._ConfigurationInvalid):
        runner._load_required_local_app_factory()


def test_invalid_arguments_fail_closed_without_loading_config_or_echoing_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _runner()
    secret = "CONTEXT-SECRET-SENTINEL"
    monkeypatch.setenv("CONTEXT_TOKEN_SECRET", secret)

    def unexpected_load() -> object:
        raise AssertionError("configuration must not be loaded for invalid arguments")

    monkeypatch.setattr(runner, "_load_required_local_app_factory", unexpected_load)

    assert runner.main(["--host", secret]) == 2
    output = capsys.readouterr()
    combined = output.out + output.err
    assert combined.strip() == "LOCAL_API_ARGUMENTS_INVALID"
    assert secret not in combined


def test_startup_failure_is_value_free_and_never_runs_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _runner()
    secret = "DATABASE-SECRET-SENTINEL"
    uvicorn_calls: list[tuple[object, int]] = []
    monkeypatch.setattr(runner, "_configure_event_loop_policy", lambda _platform: None)

    def fail_config() -> object:
        raise runner._ConfigurationInvalid(secret)

    monkeypatch.setattr(runner, "_load_required_local_app_factory", fail_config)
    monkeypatch.setattr(
        runner,
        "_run_uvicorn",
        lambda factory, port: uvicorn_calls.append((factory, port)),
    )

    assert runner.main([]) == 1
    output = capsys.readouterr()
    combined = output.out + output.err
    assert combined.strip() == "LOCAL_API_CONFIGURATION_INVALID"
    assert secret not in combined
    assert uvicorn_calls == []


def test_unexpected_server_error_is_value_free(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _runner()
    secret = "UVICORN-ERROR-SECRET-SENTINEL"

    def application_factory() -> object:
        return object()

    monkeypatch.setattr(runner, "_configure_event_loop_policy", lambda _platform: None)
    monkeypatch.setattr(
        runner,
        "_load_required_local_app_factory",
        lambda: application_factory,
    )

    def fail_server(_factory: object, _port: int) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(runner, "_run_uvicorn", fail_server)

    assert runner.main([]) == 1
    output = capsys.readouterr()
    combined = output.out + output.err
    assert combined.strip() == "LOCAL_API_START_FAILED"
    assert secret not in combined


def test_uvicorn_system_exit_and_preceding_fatal_log_are_value_free(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _runner()
    uvicorn = importlib.import_module("uvicorn")
    secret = "UVICORN-FATAL-LOG-SECRET-SENTINEL"

    def application_factory() -> object:
        return object()

    def fail_after_logging(_application: object, **_kwargs: object) -> None:
        logging.getLogger("uvicorn.error").error("fatal startup: %s", secret)
        raise SystemExit(3)

    monkeypatch.setattr(runner, "_configure_event_loop_policy", lambda _platform: None)
    monkeypatch.setattr(
        runner,
        "_load_required_local_app_factory",
        lambda: application_factory,
    )
    monkeypatch.setattr(uvicorn, "run", fail_after_logging)
    caplog.set_level(logging.ERROR, logger="uvicorn.error")

    assert runner.main([]) == 1

    output = capsys.readouterr()
    combined = output.out + output.err + caplog.text
    assert output.err.strip() == "LOCAL_API_START_FAILED"
    assert secret not in combined
