from unittest.mock import MagicMock

import pytest

from nala.athomic.resilience.retry.decorator import retry
from nala.athomic.resilience.retry.exceptions import RetryError
from nala.athomic.resilience.retry.policy import RetryPolicy


# --- Utilitários comuns ---
def patch_observability(monkeypatch):
    monkeypatch.setattr(
        "nala.athomic.observability.metrics.usage.retry_attempts_total", MagicMock()
    )
    monkeypatch.setattr(
        "nala.athomic.observability.metrics.usage.retry_failures_total", MagicMock()
    )
    monkeypatch.setattr(
        "nala.athomic.observability.metrics.usage.retry_circuit_breaker_aborts_total",
        MagicMock(),
    )
    monkeypatch.setattr(
        "nala.athomic.observability.tracing.get_tracer", lambda *a, **kw: MagicMock()
    )


# ---- TESTES --------


def test_decorator_success_after_retry(monkeypatch):
    patch_observability(monkeypatch)
    calls = {"count": 0}

    @retry(policy=RetryPolicy(attempts=3, exceptions=(ValueError,)))
    def flaky_fn():
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("fail")
        return "ok"

    assert flaky_fn() == "ok"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_decorator_async_success(monkeypatch):
    patch_observability(monkeypatch)
    calls = {"count": 0}

    @retry(policy=RetryPolicy(attempts=3, exceptions=(ValueError,)))
    async def flaky_async_fn():
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("fail async")
        return "ok"

    result = await flaky_async_fn()
    assert result == "ok"
    assert calls["count"] == 2


def test_decorator_raises_after_max_attempts(monkeypatch):
    patch_observability(monkeypatch)

    @retry(policy=RetryPolicy(attempts=2, exceptions=(ValueError,)))
    def fail_fn():
        raise ValueError("fail always")

    with pytest.raises(RetryError):
        fail_fn()


@pytest.mark.asyncio
async def test_decorator_async_raises(monkeypatch):
    patch_observability(monkeypatch)

    @retry(policy=RetryPolicy(attempts=2, exceptions=(ValueError,)))
    async def fail_async_fn():
        raise ValueError("fail async always")

    with pytest.raises(RetryError):
        await fail_async_fn()


def test_decorator_on_retry_callback(monkeypatch):
    patch_observability(monkeypatch)
    calls = []

    def on_retry(attempt, exc):
        calls.append((attempt, str(exc)))

    @retry(policy=RetryPolicy(attempts=2, exceptions=(ValueError,)), on_retry=on_retry)
    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        fn()
    assert calls and calls[0][0] == 1


def test_decorator_on_fail_callback(monkeypatch):
    patch_observability(monkeypatch)
    calls = []

    def on_fail(exc):
        calls.append(str(exc))

    @retry(policy=RetryPolicy(attempts=2, exceptions=(ValueError,)), on_fail=on_fail)
    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        fn()
    assert calls


def test_decorator_circuit_breaker(monkeypatch):
    patch_observability(monkeypatch)

    @retry(
        policy=RetryPolicy(attempts=3, exceptions=(ValueError,)),
        circuit_breaker_hook=lambda: True,
    )
    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError, match="Circuit breaker is open"):
        fn()


def test_decorator_retry_on_result(monkeypatch):
    patch_observability(monkeypatch)
    calls = {"count": 0}

    @retry(policy=RetryPolicy(attempts=3, retry_on_result=lambda r: r is None))
    def fn():
        calls["count"] += 1
        return None if calls["count"] < 3 else "ok"

    assert fn() == "ok"


def test_decorator_non_listed_exception(monkeypatch):
    patch_observability(monkeypatch)

    @retry(policy=RetryPolicy(attempts=3, exceptions=(ValueError,)))
    def fn():
        raise TypeError("not listed")

    with pytest.raises(TypeError):
        fn()


# Adicione outros testes conforme seu handler/policy permitir!
