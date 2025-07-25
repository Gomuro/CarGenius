import pytest
from app.schemas.stats.analytics import ListingSchema, TechnicalDetailsSchema, EquipmentSchema, ListingSchemaML
from app.utils import flatten_listing_ml

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]
# async def flatten_listing_ml(listings: list[ListingSchemaML]) -> list[dict]:
#     flat_listings = []
#
#     for listing in listings:
#         listing_dict = listing.dict()
#         flat_listing = ({k: v for k, v in listing_dict.items() if k not in ["technical_details", "equipment"]})
#
#         technical_details = listing_dict.get("technical_details", {}) or {}
#         equipment = listing_dict.get("equipment", {}) or {}
#
#         flat_listing.update(technical_details)
#         flat_listing.update(equipment)
#
#         for k, v in flat_listing.items():
#             if isinstance(v, bool):
#                 flat_listing[k] = int(v)
#         flat_listings.append(flat_listing)
#     return flat_listings


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
        technical_details = TechnicalDetailsSchema(category="sedan", transmission="Automatic"),
        equipment = EquipmentSchema(abs=True, speed_limiter=False)
    )
    result = await flatten_listing_ml([listing])

    assert isinstance(result, list), "Result should be a list"
    assert isinstance(result[0], dict), "Each item in the result should be a dictionary"
    print("ListingSchemaML@@@@@@@@@@@@@@", ListingSchemaML)
    print(f"Flattened result$$$$$$$$$$$$$$$: {result}")
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



