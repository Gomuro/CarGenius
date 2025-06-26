# app/tests/test_analytics.py
import os
import shutil
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # /home/.../CarGenius/server/app/tests
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # /home/.../CarGenius/server

TEST_SOURCE_PATH = os.path.join(CURRENT_DIR, "test_data", "test_car_data_Audi_1.json")
DESTINATION_PATH = os.path.join(PROJECT_ROOT, "car_data_Audi_1.json")   # path inside a Docker container


@pytest.fixture(scope="function", autouse=True)
def copy_test_json_file():
    if TEST_SOURCE_PATH != DESTINATION_PATH:
        shutil.copy(TEST_SOURCE_PATH, DESTINATION_PATH)  # copies to the project root. shutil.copy copies a file from src to dst.
    yield  # the test itself takes place here
    # if os.path.exists(DESTINATION_PATH):
    os.remove(DESTINATION_PATH)


@pytest.mark.asyncio
async def test_save_listing_to_db(client, session):
    """
    Test saving a car listing to the database.
    """
    response = await client.post("/api/v1/analytics/json-to-db")
    assert response.status_code == 200, f"Expected status code 200, got: {response.status_code}"

    data = response.json()
    print(f"Response data: {data}")
    assert "message" in data, "Response should contain 'message' key"
    assert "skipped" in data, "Response should contain 'skipped' key"
    assert "saved" in data["message"], f"Unexpected message format: {data['message']}"

    # Можна витягнути created з message, якщо треба
    import re
    match = re.search(r"saved (\d+) listings", data["message"])  # search number of saved listings
    assert match, "Message should contain number of saved listings"
    created = int(match.group(1))  # Extract the number of created listings '(\d+)' from the message

    skipped = data["skipped"]

    assert created >= 0, "Created listings should be zero or more"
    assert skipped >= 0, "Skipped listings should be zero or more"
