# server/app/tests/test_license.py
from datetime import datetime, timezone

import pytest

from app.models.license import LicenseKey
from app.services.license import generate_license_key, validate_license_key, validate_license_key_device


### Services ###
@pytest.mark.asyncio
async def test_generate_license_key(session):
    license = await generate_license_key(session, client_info="test-client")
    assert isinstance(license, LicenseKey), f"Expected LicenseKey instance, got {type(license)}"
    assert license.key is not None, "Expected license key to be generated"
    assert license.client_info == "test-client", f"Expected client_info to be 'test-client', got {license.client_info}"
    assert license.is_active is True, f"Expected is_active to be True, got {license.is_active}"
    assert license.created_at <= datetime.now(timezone.utc), f"Created at {license.created_at} is in the future"
    assert license.expires_at is not None, "Expected expires_at to be set"


@pytest.mark.asyncio
async def test_validate_license_key(session):
    license = await generate_license_key(session, client_info="test-client")
    is_valid = await validate_license_key(key=license.key, client_info="test-client", db=session)
    assert is_valid is True, "Expected license key to be valid"
    is_valid = await validate_license_key(key=license.key, client_info="wrong-client", db=session)
    assert is_valid is False, "Expected license key to be invalid for wrong client info"
    is_valid = await validate_license_key(key="non-existent-key", client_info="test-client", db=session)
    assert is_valid is False, "Expected license key to be invalid for non-existent key"


@pytest.mark.asyncio
async def test_validate_license_key_device(session):
    license = await generate_license_key(session, client_info="test-client")
    device_id = "device-123"
    # First time activation
    is_valid, message = await validate_license_key_device(
        key=license.key, device_id=device_id, client_info="test-client", db=session
    )
    assert is_valid is True, f"Expected license to be valid on first activation, got: {message}"
    assert message == "License activated and device bound"
    # Validate with the same device
    is_valid, message = await validate_license_key_device(
        key=license.key, device_id=device_id, client_info="test-client", db=session
    )
    assert is_valid is True, f"Expected license to be valid for the same device, got: {message}"
    assert message == "License key is valid"
    # Validate with a different device
    is_valid, message = await validate_license_key_device(
        key=license.key, device_id="device-456", client_info="test-client", db=session
    )
    assert is_valid is False, f"Expected license to be invalid for a different device, got: {message}"
    assert message == "Device mismatch. This license is bound to another device"


### Routers ###
@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
