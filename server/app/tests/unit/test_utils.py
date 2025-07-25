import pytest
from app.schemas.stats.analytics import TechnicalDetailsSchema, EquipmentSchema, ListingSchemaML
from app.utils import flatten_listing_ml

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_flatten_listing_ml():
    listing = ListingSchemaML(
        brand="Audi",
        model="A4",
        registration_year=2020,
        mileage=20000,
        city_or_postal_code="Kyiv",
        color="black",
        price=25000,
        url="http://test.url",
        technical_details=TechnicalDetailsSchema(category="sedan", transmission="Automatic"),
        equipment=EquipmentSchema(abs=True, speed_limiter=False)
    )
    result = await flatten_listing_ml([listing])

    assert isinstance(result, list), "Result should be a list"
    assert isinstance(result[0], dict), "Each item in the result should be a dictionary"
    assert len(result) == 1, "Should return one flattened listing"
    flat_listing = result[0]
    assert flat_listing["brand"] == "Audi"
    assert flat_listing["model"] == "A4"
    assert flat_listing["registration_year"] == 2020
    assert flat_listing["mileage"] == 20000
    assert flat_listing["city_or_postal_code"] == "Kyiv"
    assert flat_listing["color"] == "black"
    assert flat_listing["price"] == 25000
    assert flat_listing["url"] == "http://test.url"
    assert flat_listing["category"] == "sedan"
    assert flat_listing["transmission"] == "Automatic"
    assert flat_listing["abs"] == 1  # Boolean converted to int
    assert flat_listing["speed_limiter"] == 0  # Boolean converted to int


async def test_flatten_listing_ml_empty():
    result = await flatten_listing_ml([])
    assert isinstance(result, list), "Result should be a list"
    assert len(result) == 0, "Should return an empty list for no listings"
