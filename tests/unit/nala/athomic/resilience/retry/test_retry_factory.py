import pytest

from nala.athomic.resilience.retry.factory import RetryFactory


class DummyRetryPolicySettings:
    """Mock to simulate RetryPolicySettings."""

    def __init__(self, attempts, wait_min, backoff, exceptions=("Exception",)):
        self.attempts = attempts
        self.wait_min_seconds = wait_min
        self.wait_max_seconds = 60.0
        self.backoff = backoff
        self.exceptions = exceptions
        self.timeout = None
        self.jitter = None


class DummyRetrySettings:
    """Mock to simulate the new RetrySettings."""

    def __init__(self):
        self.default_policy = DummyRetryPolicySettings(
            attempts=3, wait_min=0.1, backoff=1
        )
        self.policies = {
            "special_policy": DummyRetryPolicySettings(
                attempts=5, wait_min=0.5, backoff=2
            )
        }

        class MockLogger:
            def debug(self, *args, **kwargs):
                # Mock debug method to avoid errors
                pass

            def warning(self, *args, **kwargs):
                # Mock warning method to avoid errors
                pass

            def info(self, *args, **kwargs):
                # Mock info method to avoid errors
                pass

        self.logger = MockLogger()


@pytest.fixture
def dummy_settings():
    """Provides an instance of our new configuration mock."""
    return DummyRetrySettings()


def test_factory_creates_default_policy(dummy_settings):
    """
    Checks if the factory uses 'default_policy' when no name is provided.
    """
    factory = RetryFactory(dummy_settings)
    policy = factory.create_policy()

    assert policy.attempts == 3
    assert policy.wait_min_seconds == pytest.approx(0.1)
    assert policy.backoff == 1


def test_factory_creates_named_policy(dummy_settings):
    """
    Checks if the factory correctly selects a named policy.
    This test replaces the old 'test_factory_policy_override'.
    """
    factory = RetryFactory(dummy_settings)
    policy = factory.create_policy(name="special_policy")

    assert policy.attempts == 5
    assert policy.wait_min_seconds == pytest.approx(0.5)
    assert policy.backoff == 2


def test_factory_create_retry_handler(dummy_settings):
    """
    Checks if the factory creates a RetryHandler with the correct policy.
    """
    factory = RetryFactory(dummy_settings)
    handler = factory.create_retry_handler(
        policy_name="special_policy", operation_name="test_op"
    )

    assert handler.operation_name == "test_op"
    assert handler.policy.attempts == 5
