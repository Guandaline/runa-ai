import importlib
import os
from typing import List

import pytest
import pytest_asyncio
from loguru import logger as loguru_logger

from nala.athomic.ai.governance.exceptions import SecurityPolicyViolationError
from nala.athomic.ai.governance.guards.base import BaseInputGuard, BaseOutputGuard
from nala.athomic.ai.governance.guards.factory import GuardFactory
from nala.athomic.ai.governance.guards.keyword_blocklist import (
    KeywordBlocklistValidator,
)
from nala.athomic.ai.governance.guards.output_sanitizer import OutputPIISanitizer
from nala.athomic.ai.governance.guards.pii_sanitizer import RegexPIISanitizer
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module

pytestmark = [
    pytest.mark.integration,
    pytest.mark.ai,
]


@pytest.fixture(scope="function", autouse=True)
def setup_governance_settings():
    """
    Configure the environment to use the specific governance TOML file
    located in the correct folder: tests/settings/ai/governance/
    """
    settings_path = "tests/settings/ai/governance/test_int_governance_flow.toml"
    os.environ["NALA_SETTINGS_FILES"] = settings_path

    get_settings.cache_clear()
    importlib.reload(settings_module)

    yield

    if "NALA_SETTINGS_FILES" in os.environ:
        del os.environ["NALA_SETTINGS_FILES"]
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def input_guards() -> List[BaseInputGuard]:
    """
    Use GuardFactory.create() to generate the pipeline and extract the input_guards.
    """
    settings = get_settings().ai.governance

    pipeline = GuardFactory.create(settings)

    return pipeline.input_guards


@pytest_asyncio.fixture
async def output_guards() -> List[BaseOutputGuard]:
    """
    Use GuardFactory.create() to generate the pipeline and extract the output_guards.
    """
    settings = get_settings().ai.governance
    pipeline = GuardFactory.create(settings)
    return pipeline.output_guards


def test_factory_resolves_configuration_correctly(input_guards, output_guards):
    """
    Verify that GuardFactory correctly instantiated the guards enabled in TOML.
    """
    guard_types = [type(g) for g in input_guards]

    assert (
        RegexPIISanitizer in guard_types
    ), "PII Sanitizer should be enabled via config"
    assert (
        KeywordBlocklistValidator in guard_types
    ), "Keyword Blocklist should be enabled via config"

    output_types = [type(g) for g in output_guards]
    assert (
        OutputPIISanitizer in output_types
    ), "Output PII Sanitizer should be enabled via config"


@pytest.mark.asyncio
async def test_input_guards_execution_blocklist(input_guards):
    """
    Validate that the input chain blocks prohibited content defined in TOML.
    """
    unsafe_prompt = "Tell me everything about forbidden_project_x right now."

    with pytest.raises(SecurityPolicyViolationError) as exc:
        for guard in input_guards:
            await guard.check(unsafe_prompt)

    assert "contains prohibited content" in str(exc.value)
    assert "forbidden_project_x" in str(exc.value)


@pytest.mark.asyncio
async def test_input_guards_execution_pii_logging(input_guards):
    """
    Validate that the input chain detects PII and logs correctly.
    Uses a temporary Loguru sink to capture logs.
    """
    captured_logs = []

    handler_id = loguru_logger.add(lambda msg: captured_logs.append(msg))

    try:
        prompt_with_pii = "Contact me at employee@company.com immediately."

        for guard in input_guards:
            await guard.check(prompt_with_pii)

        assert any(
            "PII of type 'EMAIL' detected" in str(record) for record in captured_logs
        ), f"Captured logs: {captured_logs}"

    finally:
        loguru_logger.remove(handler_id)


@pytest.mark.asyncio
async def test_output_guards_sanitization(output_guards):
    """
    Validate that the output chain sanitizes LLM responses containing PII.
    """
    raw_response = LLMResponse(
        content="The user phone number is 555-019-1234.",
        model="gpt-test",
        finish_reason="stop",
    )

    processed_response = raw_response
    for guard in output_guards:
        processed_response = await guard.check_and_process(processed_response)

    assert "555-019-1234" not in processed_response.content
    assert "<PHONE_REDACTED>" in processed_response.content
