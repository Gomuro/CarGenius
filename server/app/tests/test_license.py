# server/app/tests/test_license.py
import pytest

@pytest.mark.asyncio
async def test_generate_license(client):
    response = await client.post("/license/generate", json={"client_info": "test-client"})

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_validate_license(client):
    response = await client.post("/license/generate", json={"client_info": "test-client"})
    assert response.status_code == 200
    license_key = response.json()["key"]

    response = await client.post("/license/validate", json={
        "key": license_key,
        "client_info": "test-client"
    })
    assert response.status_code == 200
    assert response.json()["is_valid"] is True


# @pytest.mark.asyncio
# async def test_invalid_license(client):
#     response = await client.post("/license/validate", json={
#         "key": "invalid-key",
#         "client_info": "any"
#     })
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Invalid license key"




# import pytest
# from app.schemas.license import LicenseValidateResponse
#
#
# @pytest.mark.asyncio
# async def test_generate_and_validate_license(client):
#     # Створення ліцензії
#     response = await client.post("/license/generate", json={"client_info": "test-client"})
#     assert response.status_code == 200
#     data = response.json()
#     assert "key" in data
#     license_key = data["key"]
#
#     # Валідація ліцензії
#     validate_response = await client.post("/license/validate", json={
#         "key": license_key,
#         "client_info": "test-client"
#     })
#     assert validate_response.status_code == 200
#     assert validate_response.json() == {"is_valid": True}
#
# @pytest.mark.asyncio
# async def test_invalid_license(client):
#     response = await client.post("/license/validate", json={
#         "key": "non-existing-key",
#         "client_info": "wrong"
#     })
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Invalid license key"
