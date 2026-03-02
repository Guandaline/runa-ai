"""
Unit tests for GuardFactory.

This module tests the factory pattern implementation for creating
the GuardPipeline based on injected application settings.
"""

from unittest.mock import MagicMock, patch

import pytest

from nala.athomic.ai.governance.guards.factory import GuardFactory
from nala.athomic.ai.governance.guards.keyword_blocklist import (
    KeywordBlocklistValidator,
)
from nala.athomic.ai.governance.guards.output_sanitizer import OutputPIISanitizer
from nala.athomic.ai.governance.guards.pii_sanitizer import RegexPIISanitizer
from nala.athomic.config.schemas.ai.governance.governance_settings import (
    GovernanceRateLimitSettings,
    GovernanceSettings,
    KeywordBlocklistSettings,
    PIISanitizerSettings,
)


@pytest.fixture
def governance_settings_enabled():
    """Creates a settings object with everything enabled."""
    return GovernanceSettings(
        enabled=True,
        pii_sanitizer=PIISanitizerSettings(enabled=True, patterns={}),
        keyword_blocklist=KeywordBlocklistSettings(enabled=True, blocklist=["bad"]),
        rate_limiter=GovernanceRateLimitSettings(enabled=True),
    )


@pytest.fixture
def governance_settings_disabled():
    """Creates a settings object with the master switch disabled."""
    return GovernanceSettings(enabled=False)


@pytest.fixture
def governance_settings_partial(governance_settings_enabled):
    """
    Enabled globally, but specifically disables Keyword Blocklist.
    """
    settings = governance_settings_enabled.model_copy(deep=True)
    settings.keyword_blocklist.enabled = False
    return settings


class TestGuardFactoryCreate:
    """Test suite for GuardFactory.create method."""

    def test_create_returns_empty_pipeline_when_disabled(
        self, governance_settings_disabled
    ):
        """Verifies that an empty pipeline is returned if the master switch is off."""
        # Act
        pipeline = GuardFactory.create(governance_settings_disabled)

        # Assert
        assert not pipeline.has_input_guards
        assert not pipeline.has_output_guards
        assert len(pipeline.input_guards) == 0
        assert len(pipeline.output_guards) == 0

    @patch("nala.athomic.ai.governance.guards.factory.RateLimitGuard")
    def test_create_instantiates_all_guards_when_enabled(
        self, mock_rate_limit_cls, governance_settings_enabled
    ):
        """Verifies that all expected guards are created when settings are enabled."""
        # Arrange
        # Mock RateLimitGuard creation to avoid calling context/redis logic
        mock_instance = MagicMock()
        mock_instance.is_enabled.return_value = True
        mock_rate_limit_cls.return_value = mock_instance

        # Act
        pipeline = GuardFactory.create(governance_settings_enabled)

        # Assert
        # 1. Rate Limiter (Input)
        assert any(
            guard == mock_instance for guard in pipeline.input_guards
        ), "RateLimitGuard should be present"

        # 2. Keyword Blocklist (Input)
        assert any(
            isinstance(guard, KeywordBlocklistValidator)
            for guard in pipeline.input_guards
        ), "KeywordBlocklistValidator should be present"

        # 3. PII Sanitizer (Input)
        assert any(
            isinstance(guard, RegexPIISanitizer) for guard in pipeline.input_guards
        ), "RegexPIISanitizer should be present in input guards"

        # 4. PII Sanitizer (Output)
        assert any(
            isinstance(guard, OutputPIISanitizer) for guard in pipeline.output_guards
        ), "OutputPIISanitizer should be present in output guards"

    @patch("nala.athomic.ai.governance.guards.factory.RateLimitGuard")
    def test_create_respects_individual_toggles(
        self, mock_rate_limit_cls, governance_settings_partial
    ):
        """
        Verifies that disabling a specific guard (KeywordBlocklist) removes it
        from the pipeline even if the global switch is True.
        """
        # Arrange
        mock_instance = MagicMock()
        mock_instance.is_enabled.return_value = True
        mock_rate_limit_cls.return_value = mock_instance

        # Act
        pipeline = GuardFactory.create(governance_settings_partial)

        # Assert
        # Rate Limit should still be there
        assert any(guard == mock_instance for guard in pipeline.input_guards)

        # Keyword Blocklist should be GONE
        assert not any(
            isinstance(guard, KeywordBlocklistValidator)
            for guard in pipeline.input_guards
        ), "KeywordBlocklistValidator should NOT be present when disabled in settings"

    def test_create_filters_programmatically_disabled_guards(
        self, governance_settings_enabled
    ):
        """
        Verifies that if a Guard instance returns is_enabled()=False (internal logic),
        it is filtered out of the final pipeline.
        """
        # Arrange
        # We mock RateLimitGuard to force is_enabled=False even if settings say True
        with patch(
            "nala.athomic.ai.governance.guards.factory.RateLimitGuard"
        ) as MockRL:
            instance = MockRL.return_value
            instance.is_enabled.return_value = False

            # Act
            pipeline = GuardFactory.create(governance_settings_enabled)

            # Assert
            assert not any(
                guard == instance for guard in pipeline.input_guards
            ), "Guards reporting is_enabled()=False should be filtered out"

    def test_create_injects_pipeline_settings(self, governance_settings_enabled):
        """Verifies that pipeline settings are correctly passed to the GuardPipeline."""
        # Arrange
        governance_settings_enabled.pipeline.fail_fast = False

        # Act
        pipeline = GuardFactory.create(governance_settings_enabled)

        # Assert
        assert pipeline.settings.fail_fast is False
