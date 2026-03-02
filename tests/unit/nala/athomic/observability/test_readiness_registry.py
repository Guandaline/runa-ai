import pytest

from nala.athomic.observability.health.protocol import ReadinessCheck
from nala.athomic.observability.health.registry import ReadinessRegistry


class AlwaysOkCheck(ReadinessCheck):
    name = "ok"

    def enabled(self) -> bool:
        return True

    async def check(self) -> bool:
        return True


class AlwaysFailCheck(ReadinessCheck):
    name = "fail"

    def enabled(self) -> bool:
        return True

    async def check(self) -> bool:
        return False


class SkippedCheck(ReadinessCheck):
    name = "skipped"

    def enabled(self) -> bool:
        return False

    async def check(self) -> bool:
        return True  # shouldn't run


class ErrorCheck(ReadinessCheck):
    name = "error"

    def enabled(self) -> bool:
        return True

    async def check(self) -> bool:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_readiness_registry_results():
    registry = ReadinessRegistry()
    registry.register(AlwaysOkCheck())
    registry.register(AlwaysFailCheck())
    registry.register(SkippedCheck())
    registry.register(ErrorCheck())

    result = await registry.run_all()

    assert result["ok"] == "ok"
    assert result["fail"] == "fail"
    assert result["skipped"] == "skipped"
    assert result["error"] == "fail"
