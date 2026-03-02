# tests/unit/nala/athomic/context/test_key_resolver.py
from unittest.mock import MagicMock

import pytest

from nala.athomic.config.schemas.context.context_config import ContextSettings
from nala.athomic.context.generator import ContextKeyGenerator

EXECUTION_CONTEXT_PATH = "nala.athomic.context.generator.ExecutionContext"


@pytest.fixture
def mock_execution_context(monkeypatch) -> MagicMock:
    """
    Creates a mock for the ExecutionContext class to control the values of tenant_id and user_id
    that are returned within the ContextKeyGenerator.
    """
    mock = MagicMock()
    instance = mock.return_value
    instance.tenant_id = None
    instance.user_id = None

    monkeypatch.setattr(EXECUTION_CONTEXT_PATH, mock)
    return instance


@pytest.mark.parametrize(
    "config, context_values, key_parts, expected_key",
    [
        (
            {},
            {"tenant_id": "tenant-ignored", "user_id": None},
            ["my-key"],
            "nala:default:my-key",
        ),
        # Scenario 2: Tenant enabled, tenant in context, user disabled -> TENANT INCLUDED
        (
            {"multi_tenancy_enabled": True},
            {"tenant_id": "tenant-42", "user_id": "user-123"},
            ["abc"],
            "nala:tenant-42:default:abc",
        ),
        # Scenario 3: Tenant and User enabled and present in context -> BOTH INCLUDED
        (
            {"multi_tenancy_enabled": True, "use_user_uid": True},
            {"tenant_id": "tenant-x", "user_id": "user-123"},
            ["limit"],
            "nala:tenant-x:user-123:default:limit",
        ),
        # Scenario 4: Tenant disabled, but present in context -> TENANT IGNORED
        (
            {"multi_tenancy_enabled": False},
            {"tenant_id": "tenant-ignored", "user_id": None},
            ["key"],
            "nala:default:key",
        ),
        # Scenario 5: Custom namespace, prefix and separator with tenant enabled -> CUSTOM + TENANT INCLUDED
        (
            {"static_prefix": "myapp", "separator": "|", "multi_tenancy_enabled": True},
            {"tenant_id": "t1", "user_id": None},
            ["data", "item1"],
            "myapp|t1|default|data|item1",
        ),
        # Scenario 6: Tenant and User enabled, but only tenant in context -> ONLY TENANT INCLUDED
        (
            {"multi_tenancy_enabled": True, "use_user_uid": True},
            {"tenant_id": "t1", "user_id": None},
            ["item"],
            "nala:t1:default:item",
        ),
        # Scenario 7: All context disabled in config -> NO CONTEXT INCLUDED
        (
            {"multi_tenancy_enabled": False, "use_user_uid": False},
            {"tenant_id": "t1", "user_id": "u1"},
            ["general", "setting"],
            "nala:default:general:setting",
        ),
    ],
)
def test_key_generation_scenarios(
    mock_execution_context: MagicMock,
    config: dict,
    context_values: dict,
    key_parts: list,
    expected_key: str,
):
    """
    Tests various key generation scenarios using parametrization.
    """
    # Arrange
    mock_execution_context.tenant_id = context_values["tenant_id"]
    mock_execution_context.user_id = context_values["user_id"]

    # Arrange
    context_settings = ContextSettings(**config)
    resolver = ContextKeyGenerator(settings=context_settings)

    # Act
    generated_key = resolver.generate(*key_parts)

    # Assert
    assert generated_key == expected_key


def test_custom_namespace_is_used(mock_execution_context: MagicMock):
    """
    Tests if the namespace provided during instantiation takes precedence
    over the one in the settings object.
    """
    # Arrange
    mock_execution_context.tenant_id = "tenant-1"
    context_settings = ContextSettings(
        namespace="settings_namespace", multi_tenancy_enabled=True
    )

    resolver = ContextKeyGenerator(
        settings=context_settings, namespace="instance_namespace"
    )

    # Act
    key = resolver.generate("my-key")

    # Assert
    assert key == "nala:tenant-1:instance_namespace:my-key"
