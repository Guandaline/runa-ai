import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_metrics(client: AsyncClient) -> None:
    """
    Validates that the internal metrics endpoint is accessible and correctly
    exposes Prometheus-formatted metrics as byte content.
    """
    response = await client.get("/internal/metrics")

    assert response.status_code == 200
    assert b"api_requests_total" in response.content
