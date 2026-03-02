import asyncio
from unittest.mock import MagicMock

import pytest

from nala.athomic.resilience.retry.handler import RetryError, RetryHandler, RetryPolicy


@pytest.fixture
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
    tracer_mock = MagicMock()
    tracer_mock.get_current_span.return_value = None
    monkeypatch.setattr(
        "nala.athomic.observability.tracing.get_tracer", lambda *a, **kw: tracer_mock
    )


# Utilitários para sync e async
def always_fail():
    raise ValueError("fail")


async def always_fail_async():
    raise ValueError("fail async")


def succeed_after_n(n, exception=ValueError):
    attempts = {"count": 0}

    def fn():
        attempts["count"] += 1
        if attempts["count"] < n:
            raise exception("fail")
        return "ok"

    return fn


async def succeed_after_n_async(n, exception=ValueError):
    attempts = {"count": 0}
    await asyncio.sleep(0)

    async def fn():
        await asyncio.sleep(0.1)
        attempts["count"] += 1
        if attempts["count"] < n:
            raise exception("fail async")
        return "ok"

    return fn


# ----------- TESTES ----------------


def test_retry_success_after_failures(patch_observability):
    handler = RetryHandler(RetryPolicy(attempts=3))
    fn = succeed_after_n(2)
    result = handler.run(fn)
    assert result == "ok"


@pytest.mark.asyncio
async def test_async_retry_success_after_failures(patch_observability):
    handler = RetryHandler(RetryPolicy(attempts=3))
    fn = await succeed_after_n_async(2)
    result = await handler.arun(fn)
    assert result == "ok"


def test_retry_raises_after_max_attempts(patch_observability):
    handler = RetryHandler(RetryPolicy(attempts=2))
    with pytest.raises(RetryError):
        handler.run(always_fail)


@pytest.mark.asyncio
async def test_async_retry_raises_after_max_attempts(patch_observability):
    handler = RetryHandler(RetryPolicy(attempts=2))
    with pytest.raises(RetryError):
        await handler.arun(always_fail_async)


def test_retry_callback(patch_observability):
    retry_calls = []

    def on_retry(attempt, exc):
        retry_calls.append((attempt, str(exc)))

    handler = RetryHandler(RetryPolicy(attempts=2), on_retry=on_retry)
    with pytest.raises(RetryError):
        handler.run(always_fail)
    assert retry_calls and retry_calls[0][0] == 1


def test_fail_callback(patch_observability):
    fail_called = []

    def on_fail(exc):
        fail_called.append(str(exc))

    handler = RetryHandler(RetryPolicy(attempts=2), on_fail=on_fail)
    with pytest.raises(RetryError):
        handler.run(always_fail)
    assert fail_called


def test_circuit_breaker_abort(patch_observability):
    handler = RetryHandler(RetryPolicy(attempts=3), circuit_breaker_hook=lambda: True)
    with pytest.raises(RetryError, match="Circuit breaker is open"):
        handler.run(always_fail)


@pytest.mark.asyncio
async def test_async_timeout(patch_observability):
    async def slow():
        await asyncio.sleep(1)

    handler = RetryHandler(RetryPolicy(attempts=1, timeout=0.01))
    with pytest.raises(RetryError):
        await handler.arun(slow)


def test_keyboard_interrupt_not_captured(patch_observability):
    def raises_keyboard():
        raise KeyboardInterrupt

    handler = RetryHandler(RetryPolicy(attempts=2))
    with pytest.raises(KeyboardInterrupt):
        handler.run(raises_keyboard)


def test_retry_multiple_exceptions(patch_observability):
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("fail1")
        if calls["count"] == 2:
            raise RuntimeError("fail2")
        return "ok"

    handler = RetryHandler(
        RetryPolicy(attempts=3, exceptions=(ValueError, RuntimeError))
    )
    assert handler.run(fn) == "ok"


@pytest.mark.asyncio
async def test_async_retry_and_fail_callbacks(patch_observability):
    retry_calls = []
    fail_calls = []

    async def fn():
        raise ValueError("fail")

    handler = RetryHandler(
        RetryPolicy(attempts=2, exceptions=(ValueError,)),
        on_retry=lambda attempt, exc: retry_calls.append((attempt, str(exc))),
        on_fail=lambda exc: fail_calls.append(str(exc)),
    )

    with pytest.raises(RetryError):
        await handler.arun(fn)

    assert len(retry_calls) == 1
    assert len(fail_calls) == 1
    assert "fail" in fail_calls[0]


def test_retry_on_result(patch_observability):
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        return None if calls["count"] < 3 else "ok"

    handler = RetryHandler(RetryPolicy(attempts=3, retry_on_result=lambda r: r is None))
    assert handler.run(fn) == "ok"


def test_circuit_breaker_disabled(patch_observability):
    def fn():
        raise ValueError("fail")

    handler = RetryHandler(RetryPolicy(attempts=2))
    with pytest.raises(RetryError):
        handler.run(fn)


def test_retry_backoff(patch_observability):
    # Não testamos tempo real, mas garantimos que a policy aceita parâmetros de backoff sem falhar
    def fn():
        raise ValueError("fail")

    handler = RetryHandler(
        RetryPolicy(
            attempts=2, wait_min_seconds=0.01, wait_max_seconds=0.1, backoff=0.01
        )
    )
    with pytest.raises(RetryError):
        handler.run(fn)


def test_retry_disable_observability_duplicate(monkeypatch):
    # Não deve acessar métricas/tracing
    monkeypatch.setattr(
        "nala.athomic.observability.metrics.usage.retry_attempts_total",
        MagicMock(side_effect=Exception("Should not be called")),
    )
    monkeypatch.setattr(
        "nala.athomic.observability.metrics.usage.retry_failures_total",
        MagicMock(side_effect=Exception("Should not be called")),
    )
    monkeypatch.setattr(
        "nala.athomic.observability.metrics.usage.retry_circuit_breaker_aborts_total",
        MagicMock(side_effect=Exception("Should not be called")),
    )
    monkeypatch.setattr(
        "nala.athomic.observability.tracing.get_tracer",
        lambda *a, **kw: MagicMock(side_effect=Exception("Should not be called")),
    )

    def fn():
        raise ValueError("fail")

    handler = RetryHandler(RetryPolicy(attempts=1))
    with pytest.raises(RetryError):
        handler.run(fn)


def test_non_listed_exception_not_retried(patch_observability):
    def fn():
        raise TypeError("not listed")

    handler = RetryHandler(RetryPolicy(attempts=3, exceptions=(ValueError,)))
    with pytest.raises(TypeError) as excinfo:
        handler.run(fn)
    assert "not listed" in str(excinfo.value)


def test_attempts_one(patch_observability):
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        return "ok"

    handler = RetryHandler(RetryPolicy(attempts=1))
    assert handler.run(fn) == "ok"
    assert calls["count"] == 1


def test_attempts_zero(patch_observability):
    with pytest.raises(ValueError, match="Attempts must be at least 1"):
        RetryHandler(RetryPolicy(attempts=0))


def test_sync_with_timeout(patch_observability):
    def fn():
        return "ok"

    handler = RetryHandler(RetryPolicy(attempts=1, timeout=0.01))
    assert handler.run(fn) == "ok"


@pytest.mark.asyncio
async def test_async_retry_on_result(patch_observability):
    calls = {"count": 0}

    async def fn():
        await asyncio.sleep(0.1)
        calls["count"] += 1
        return None if calls["count"] < 2 else "ok"

    handler = RetryHandler(RetryPolicy(attempts=3, retry_on_result=lambda r: r is None))
    assert await handler.arun(fn) == "ok"


def test_tracing_with_active_span(patch_observability):
    class FakeSpan:
        def __init__(self):
            self.events = []

        def add_event(self, event, attrs=None):
            self.events.append((event, attrs))

    span = FakeSpan()

    class TracerFake:
        def get_current_span(self):
            return span

    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("fail")
        return "ok"

    tracer = TracerFake()
    handler = RetryHandler(RetryPolicy(attempts=2), tracer=tracer)
    assert handler.run(fn) == "ok"
    assert span.events, "Tracing event should be registered in span.events"
