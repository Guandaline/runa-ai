import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from nala.athomic.resilience.retry.exceptions import RetryError
from nala.athomic.resilience.retry.handler import RetryHandler
from nala.athomic.resilience.retry.policy import RetryPolicy

# ----------------- UTILIDADES ----------------------


@pytest.fixture
def real_policy():
    return RetryPolicy(
        attempts=2,
        exceptions=(ValueError,),
        backoff=1.0,
        wait_min_seconds=0.01,
        wait_max_seconds=0.05,
    )


# ----------------- TESTES -------------------------


def test_on_retry_callback_failure():
    def fn():
        raise ValueError("fail")

    def bad_callback(attempt, exc):
        raise RuntimeError("callback exploded!")

    handler = RetryHandler(RetryPolicy(attempts=2), on_retry=bad_callback)
    with pytest.raises(RetryError):
        handler.run(fn)
    # Esperado: RetryHandler ignora falha no callback


def test_on_fail_callback_failure():
    def fn():
        raise ValueError("fail")

    def bad_fail_callback(exc):
        raise RuntimeError("fail-callback exploded!")

    handler = RetryHandler(RetryPolicy(attempts=1), on_fail=bad_fail_callback)
    with pytest.raises(RetryError):
        handler.run(fn)


def test_retry_with_multiple_predicates():
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("fail")
        elif calls["count"] == 2:
            return None
        return "ok"

    handler = RetryHandler(
        RetryPolicy(
            attempts=3, exceptions=(ValueError,), retry_on_result=lambda x: x is None
        )
    )
    assert handler.run(fn) == "ok"


def test_circuit_breaker_opens_midway():
    # CB aberto apenas após 1 tentativa
    state = {"open": False}

    def cb():
        was = state["open"]
        state["open"] = True
        return was  # False na primeira, True nas demais

    def fn():
        raise ValueError("fail")

    handler = RetryHandler(
        RetryPolicy(attempts=3, exceptions=(ValueError,)), circuit_breaker_hook=cb
    )
    with pytest.raises(RetryError, match="Circuit breaker is open"):
        handler.run(fn)


@pytest.mark.asyncio
async def test_async_timeout_triggers():
    async def fn():
        await asyncio.sleep(2)
        return "ok"

    handler = RetryHandler(RetryPolicy(attempts=2, timeout=0.1))
    with pytest.raises(RetryError):
        await handler.arun(fn)


def test_attempts_one_disables_retry():
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        raise ValueError("fail")

    handler = RetryHandler(RetryPolicy(attempts=1))
    with pytest.raises(RetryError):
        handler.run(fn)
    assert calls["count"] == 1


def test_metric_counters_are_incremented(monkeypatch):
    from nala.athomic.resilience.retry import handler as retry_handler_mod

    metric = MagicMock()
    monkeypatch.setattr(retry_handler_mod, "retry_attempts_total", metric)

    policy = RetryPolicy(attempts=2)
    handler = RetryHandler(policy)

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)

    assert metric.labels.call_count > 0


def test_policy_invalid_attempts_zero():
    with pytest.raises(ValueError):
        RetryPolicy(attempts=0)


def test_retry_on_result_accepts_and_rejects():
    results = [None, 0, 1, 2, "ok"]
    retried = []

    def fn():
        v = results.pop(0)
        if v is None or v == 0:
            retried.append(v)
        return v

    handler = RetryHandler(
        RetryPolicy(attempts=5, retry_on_result=lambda x: x is None or x == 0)
    )
    assert handler.run(fn) == 1  # Para no primeiro resultado válido


def test_operation_name_is_used():
    logs = []

    class FakeLogger:
        def bind(self, **kwargs):
            return self

        def warning(self, msg, *a, **kw):
            logs.append(msg)

        def error(self, msg, *a, **kw):
            logs.append(msg)

    fake_logger = FakeLogger()
    handler = RetryHandler(
        RetryPolicy(attempts=2),
        operation_name="my_op",
        logger=fake_logger,  # <---- agora direto!
    )

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)
    assert any("my_op" in msg for msg in logs), f"Logs gerados: {logs}"


def test_exception_not_listed_propagates():
    def fn():
        raise TypeError("not listed")

    handler = RetryHandler(RetryPolicy(attempts=3, exceptions=(ValueError,)))
    with pytest.raises(TypeError):
        handler.run(fn)


def test_args_and_kwargs_passed():
    def fn(a, b, kw=None):
        assert a == 10 and b == 20 and kw == "foo"
        raise ValueError("fail")

    handler = RetryHandler(RetryPolicy(attempts=1))
    with pytest.raises(RetryError):
        handler.run(fn, 10, 20, kw="foo")


def test_jitter_backoff_does_not_crash():
    # Apenas garante que não crasha com jitter/backoff
    handler = RetryHandler(RetryPolicy(attempts=2, backoff=3.0, jitter=0.9))

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)


def test_circuit_breaker_disabled():
    def fn():
        raise ValueError("fail")

    handler = RetryHandler(RetryPolicy(attempts=2), circuit_breaker_hook=None)
    with pytest.raises(RetryError):
        handler.run(fn)


def test_tracing_with_active_span(real_policy):
    class FakeSpan:
        def __init__(self):
            self.events = []

        def add_event(self, event, attrs=None):
            self.events.append((event, attrs))

    span = FakeSpan()

    class Tracer:
        def get_current_span(self):
            return span

    tracer = Tracer()
    handler = RetryHandler(real_policy, tracer=tracer)  # <--- injeta diretamente

    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("fail")
        return "ok"

    assert handler.run(fn) == "ok"
    assert span.events, "Tracing event should be registered in span.events"
    # Opcional: checar conteúdo
    assert any("retry" in event for event, _ in span.events), f"Events: {span.events}"


@pytest.mark.asyncio
async def test_async_retry_on_result():
    results = [None, None, "final"]

    async def fn():
        await asyncio.sleep(0.1)  # Simula operação assíncrona
        return results.pop(0)

    handler = RetryHandler(RetryPolicy(attempts=3, retry_on_result=lambda x: x is None))
    assert await handler.arun(fn) == "final"


def test_retry_success_on_second_attempt(real_policy):
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("fail")
        return "ok"

    handler = RetryHandler(real_policy)
    assert handler.run(fn) == "ok"
    assert calls["count"] == 2


def test_retry_raises_after_max_attempts(real_policy):
    def always_fail():
        raise ValueError("fail")

    handler = RetryHandler(real_policy)
    with pytest.raises(RetryError):
        handler.run(always_fail)


def test_retry_on_result_with_real_policy(real_policy: RetryPolicy):
    results = [None, None, "ok"]
    policy = RetryPolicy(
        attempts=5,
        exceptions=(ValueError,),
        retry_on_result=lambda x: x is None,
        backoff=real_policy.backoff,
        wait_min_seconds=real_policy.wait_min_seconds,
        wait_max_seconds=real_policy.wait_max_seconds,
    )

    handler = RetryHandler(policy)

    def fn():
        return results.pop(0)

    assert handler.run(fn) == "ok"


@pytest.mark.parametrize(
    "results, retry_on_result, expected, total_attempts",
    [
        ([None, "ok"], lambda x: x is None, "ok", 2),
        ([0, 0, "ok"], lambda x: x == 0, "ok", 3),
        ([None, None, 1], lambda x: x is None, 1, 3),
        (["bad", "good"], lambda x: x == "bad", "good", 2),
    ],
)
def test_retry_on_result_various(results, retry_on_result, expected, total_attempts):
    calls = {"count": 0}
    data = results.copy()

    def fn():
        calls["count"] += 1
        return data.pop(0)

    handler = RetryHandler(RetryPolicy(attempts=5, retry_on_result=retry_on_result))
    assert handler.run(fn) == expected
    assert calls["count"] == total_attempts


def test_circuit_breaker_always_open():
    def cb():
        return True  # Sempre aberto

    def fn():
        raise ValueError("fail")

    handler = RetryHandler(
        RetryPolicy(attempts=3, exceptions=(ValueError,)), circuit_breaker_hook=cb
    )
    with pytest.raises(RetryError, match="Circuit breaker is open"):
        handler.run(fn)


def test_circuit_breaker_never_opens():
    def cb():
        return False

    attempts = []

    def fn():
        attempts.append(1)
        raise ValueError("fail")

    handler = RetryHandler(
        RetryPolicy(attempts=2, exceptions=(ValueError,)), circuit_breaker_hook=cb
    )
    with pytest.raises(RetryError):
        handler.run(fn)
    assert len(attempts) == 2


def test_backoff_and_jitter(monkeypatch):
    sleep_times = []

    monkeypatch.setattr("time.sleep", lambda t: sleep_times.append(t))

    handler = RetryHandler(
        RetryPolicy(
            attempts=3,
            backoff=2.0,
            wait_min_seconds=0.01,
            wait_max_seconds=0.05,
            jitter=0.5,
        )
    )

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)
    # sleep_times deve ter ao menos 2 valores (n tentativas - 1)
    assert len(sleep_times) == 2
    assert all(
        0.01 <= t <= 0.05 for t in sleep_times
    )  # Com jitter, mas dentro dos limites


def test_on_retry_callback_error_logged():
    logs = []

    class FakeLogger:
        def bind(self, **kwargs):
            return self

        def error(self, msg, *a, **kw):
            logs.append(msg)

        def warning(self, *a, **k):
            # Not implemented
            pass

    def bad_callback(attempt, exc):
        raise RuntimeError("BOOM")

    handler = RetryHandler(
        RetryPolicy(attempts=2),
        on_retry=bad_callback,
        logger=FakeLogger(),
    )

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)

    assert any("Retry callback raised" in msg for msg in logs)


def test_on_fail_callback_error_logged():
    logs = []

    class FakeLogger:
        def bind(self, **kwargs):
            return self

        def error(self, msg, *a, **kw):
            logs.append(msg)

        def warning(self, *a, **k):
            # Not implemented
            pass

    def bad_fail_callback(exc):
        raise RuntimeError("FAIL-BOOM")

    handler = RetryHandler(
        RetryPolicy(attempts=1),
        on_fail=bad_fail_callback,
        logger=FakeLogger(),
    )

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)

    assert any("Fail callback raised" in msg for msg in logs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "results, retry_on_result, expected",
    [
        ([None, None, "ok"], lambda x: x is None, "ok"),
        ([0, 1], lambda x: x == 0, 1),
    ],
)
async def test_async_retry_on_result_param(results, retry_on_result, expected):
    data = results.copy()

    async def fn():
        await asyncio.sleep(0.01)
        return data.pop(0)

    handler = RetryHandler(RetryPolicy(attempts=5, retry_on_result=retry_on_result))
    assert await handler.arun(fn) == expected


def test_retry_handler_thread_safe():
    results = []

    def target():
        handler = RetryHandler(RetryPolicy(attempts=2))
        try:

            def fn():
                raise ValueError("fail")

            handler.run(fn)
        except RetryError:
            results.append("done")

    threads = [threading.Thread(target=target) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results == ["done"] * 10


def test_logger_context():
    class ContextLogger:
        def __init__(self):
            self.context = []

        def bind(self, **kwargs):
            self.context.append(kwargs)
            return self

        def warning(self, msg, *a, **k):
            # Not implemented
            pass

        def error(self, msg, *a, **k):
            # Not implemented
            pass

    logger = ContextLogger()
    handler = RetryHandler(RetryPolicy(attempts=1), logger=logger)

    def fn():
        raise ValueError("fail")

    with pytest.raises(RetryError):
        handler.run(fn)
    # Garante que operation está no contexto
    assert any("operation" in c for c in logger.context)


def test_keyboardinterrupt_not_caught():
    handler = RetryHandler(RetryPolicy(attempts=2))

    def fn():
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        handler.run(fn)
