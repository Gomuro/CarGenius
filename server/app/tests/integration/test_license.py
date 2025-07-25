# server/app/tests/test_license.py
from datetime import datetime, timezone
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_generate_and_validate_license(client):
    # Generate license
    response = await client.post("/api/v1/license/generate", json={"client_info": "test-client"})
    assert response.status_code == 200
    license_key = response.json()["key"]

    # Validate license
    response = await client.post("/api/v1/license/validate", json={
        "key": license_key,
        "client_info": "test-client"
    })
    if response.status_code != 200:
        print("Validate response:", response.status_code, response.text)
    assert response.status_code == 200, f"Unexpected status: {response.status_code}, body: {response.text}"  #
    assert response.json()["is_valid"] is True


async def test_generate_license(client):
    # Generate license
    response = await client.post("/api/v1/license/generate", json={"client_info": "test-client"})
    assert response.status_code == 200, f"Unexpected status: {response.status_code}, body: {response.text}"
    data = response.json()  # Parse the JSON response
    assert "key" in data, f"Response does not contain 'key': {data}"
    assert data["is_active"] is True, f"Expected 'is_active' to be True, got {data['is_active']}"
    assert data["client_info"] == "test-client", f"Expected 'test-client', got {data['client_info']}"
    assert datetime.fromisoformat(data["created_at"]) <= datetime.now(
        timezone.utc), f"Created at {data['created_at']} is in the future"
