import pytest

from nala.athomic.resilience.retry.adapter import (
    create_policy_from_settings,
    resolve_exceptions,
)
from nala.athomic.resilience.retry.policy import RetryPolicy


class DummyRetrySettings:
    attempts = 3
    wait_min_seconds = 0.01
    wait_max_seconds = 0.1
    backoff = 2.0
    jitter = 0.1
    timeout = 1.5


def test_resolve_exceptions_with_strings():
    # Deve resolver nomes builtins
    excs = resolve_exceptions(["ValueError", "RuntimeError"])
    assert excs == (ValueError, RuntimeError)


def test_resolve_exceptions_with_types():
    excs = resolve_exceptions([ValueError, RuntimeError])
    assert excs == (ValueError, RuntimeError)


def test_resolve_exceptions_mixed():
    excs = resolve_exceptions(["ValueError", RuntimeError])
    assert excs == (ValueError, RuntimeError)


def test_resolve_exceptions_invalid_type():
    with pytest.raises(TypeError):
        resolve_exceptions([123, "ValueError"])


def test_resolve_exceptions_unknown_name():
    with pytest.raises(ValueError):
        resolve_exceptions(["NotARealException"])


def test_create_policy_from_settings_with_string_names():
    class S(DummyRetrySettings):
        exceptions = ("ValueError",)

    policy = create_policy_from_settings(S)
    assert isinstance(policy, RetryPolicy)
    assert policy.exceptions == (ValueError,)


def test_create_policy_from_settings_with_types():
    class S(DummyRetrySettings):
        exceptions = (ValueError,)

    policy = create_policy_from_settings(S)
    assert isinstance(policy, RetryPolicy)
    assert policy.exceptions == (ValueError,)


def test_create_policy_from_settings_mixed():
    class S(DummyRetrySettings):
        exceptions = ("ValueError", RuntimeError)

    policy = create_policy_from_settings(S)
    assert isinstance(policy, RetryPolicy)
    assert policy.exceptions == (ValueError, RuntimeError)


def test_create_policy_from_settings_invalid():
    class S(DummyRetrySettings):
        exceptions = (123,)

    with pytest.raises(TypeError):
        create_policy_from_settings(S)


def test_create_policy_from_settings_unknown():
    class S(DummyRetrySettings):
        exceptions = ("NotARealException",)

    with pytest.raises(ValueError):
        create_policy_from_settings(S)
