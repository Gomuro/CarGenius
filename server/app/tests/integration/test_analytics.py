# app/tests/test_analytics.py
import os
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import delete

from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.models.license import LicenseKey

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_save_listing_to_db(client, session):
    """
    Test saving a car listing to the database.
    """
    assert os.path.exists("car_data_Audi_1.json"), "Test data file is missing!"
    response = await client.post("/api/v1/analytics/json-to-db")
    assert response.status_code == 200, f"Expected status code 200, got: {response.status_code}"

    data = response.json()
    print(f"Response data: {data}")
    assert "message" in data, "Response should contain 'message' key"
    assert "skipped" in data, "Response should contain 'skipped' key"
    assert "saved" in data["message"], f"Unexpected message format: {data['message']}"

    # You can extract 'created' from the message if needed
    import re
    match = re.search(r"saved (\d+) listings", data["message"])  # search number of saved listings
    assert match, "Message should contain number of saved listings"
    created = int(match.group(1))  # Extract the number of created listings '(\d+)' from the message

    skipped = data["skipped"]

    assert created >= 0, "Created listings should be zero or more"
    assert skipped >= 0, "Skipped listings should be zero or more"


async def test_get_models_for_brand(client, session):
    response = await client.get("/api/v1/analytics/filter-options/models?brand=Audi")
    assert response.status_code == 200, f"Expected status code 200, got: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "Expected non-empty list of models"
    assert "A6" in data, "Expected model 'A6' to be in the list of models for brand 'Audi'"


async def test_get_colors_for_filters(client, session):
    response = await client.get("/api/v1/analytics/filter-options/colors?brand=Audi&model=A6")
    assert response.status_code == 200, f"Expected status code 200, got: {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "Expected non-empty list of colors"
    assert "Black" in data, "Expected color 'Black' to be in the list of colors for Audi A6"
    # assert "Schwarz" in data, "Expected color 'Schwarz' to be in the list of colors for Audi A6"


async def test_get_filter_options(client, session):
    await session.execute(delete(ListingMobileDe))
    await session.execute(delete(TechnicalDetails))
    await session.execute(delete(Equipment))
    await session.commit()
    # Creating test records in the database
    session.add_all([
        ListingMobileDe(brand="Audi", model="Q8", registration_year=2024, color="Gray", price=60000,
                        url=f"https://example.com/audi-a6-{uuid.uuid4()}", is_active=True),
        ListingMobileDe(brand="Audi", model="A4", registration_year=2022, color="Black", price=25000,
                        # ListingMobileDe(brand="Audi", model="A4", registration_year=2022, color="Schwarz", price=25000,
                        url=f"https://example.com/audi-a6-{uuid.uuid4()}", is_active=True),
        ListingMobileDe(brand="BMW", model="X5", registration_year=2023, color="White", price=45000,
                        url=f"https://example.com/audi-a6-{uuid.uuid4()}", is_active=True),
        ListingMobileDe(brand="Inactive", model="Z", registration_year=2021, color="Blue", price=10000,
                        url=f"https://example.com/audi-a6-{uuid.uuid4()}", is_active=False),
    ])
    await session.commit()

    # Request to endpoint
    response = await client.get("/api/v1/analytics/filter-options")
    assert response.status_code == 200

    data = response.json()

    # Checking only active records with non -expensive fields
    assert "brands" in data
    assert sorted(data["brands"]) == ["Audi", "BMW"]

    assert "models" in data
    assert sorted(data["models"]) == ["A4", "Q8", "X5"]

    assert "colors" in data
    # assert sorted(data["colors"]) == ["Gray", "Schwarz", "White"]
    assert sorted(data["colors"]) == ['Black', 'Gray', 'White']

    assert "years" in data
    assert sorted(data["years"], reverse=True) == [2024, 2023, 2022]

    assert "price_range" in data
    assert data["price_range"]["min"] == 25000
    assert data["price_range"]["max"] == 60000


async def test_license_per_day(client, session):
    # Clear previous license keys
    await session.execute(delete(LicenseKey))
    await session.commit()

    # Add test license keys
    for i in range(5):
        license_key = LicenseKey(
            key=f"test-license-key-{i}",  # Unique key for each license
            created_at=datetime(2025, 6, i + 1, 0, 0, 0, tzinfo=timezone.utc),  # Simulating different creation dates
        )
        session.add(license_key)
        await session.commit()

        # Request to endpoint
        response = await client.get("/api/v1/stats/licenses-per-day?days=60")

        assert response.status_code == 200, f"Expected status code 200, got: {response.status_code}"
        data = response.json()
        for i, row in enumerate(data):
            assert row["date"] == f"2025-06-{i + 1:02}", f"Expected date '2025-06-{i + 1}', got: {row['date']}"
            assert row["count"] == 1, f"Expected count 1 for each date, got: {row['count']}"
            assert isinstance(row["count"], int)
    assert isinstance(data, list)  # Check that the response is a list
    assert len(data) == 5, f"Expected 5 license keys, got: {len(data)}"
    dates = [row["date"] for row in data]
    assert dates == sorted(dates), "Dates should be sorted in ascending order"
    assert len(set(dates)) == len(dates), "Dates should be unique"

    # Edge case: No license keys created
    await session.execute(delete(LicenseKey))
    await session.commit()
    response = await client.get("/api/v1/stats/licenses-per-day?days=60")
    assert response.status_code == 200, f"Expected status code 200, got: {response.status_code}"
    assert response.json() == [], "Expected empty list when no license keys are created"
