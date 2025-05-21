# server/app/tests/test_license.py
import pytest


@pytest.mark.asyncio
async def test_generate_and_validate_license(client):
    # Generate license
    response = await client.post("/license/generate", json={"client_info": "test-client"})
    assert response.status_code == 200
    license_key = response.json()["key"]

    # Validate license
    response = await client.post("/license/validate", json={
        "key": license_key,
        "client_info": "test-client"
    })
    if response.status_code != 200:
        print("Validate response:", response.status_code, response.text)
    assert response.status_code == 200, f"Unexpected status: {response.status_code}, body: {response.text}"
    assert response.json()["is_valid"] is True
