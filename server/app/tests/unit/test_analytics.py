# app/tests/test_analytics.py
import uuid
from uuid import uuid4
import pytest
from sqlalchemy import delete

from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.models.license import LicenseKey
from app.schemas.stats.analytics import ListingSchemaML, ListingSchema, TechnicalDetailsSchema, EquipmentSchema, \
    ListingFilteredResponse
from app.services.stats.analytics import get_filtered_for_ml, get_filtered

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_get_filtered_for_ml(session):
    await session.execute(delete(ListingMobileDe))
    await session.execute(delete(TechnicalDetails))
    await session.execute(delete(Equipment))
    await session.commit()

    listing = ListingMobileDe(
        brand="Audi",
        model="A6",
        registration_year=2024,
        price=45000,
        mileage=30000,
        city_or_postal_code="Berlin",
        color="Schwarz",
        url=f"https://example.com/audi-a6-{uuid4()}",
    )
    session.add(listing)
    await session.flush()  # Get the ID of the listing after flushing

    tech = TechnicalDetails(
        listing_id=listing.id,  # Use the ID of the listing created above
        engine_type="Elektro",
        battery_range=500
    )
    equipment = Equipment(
        listing_id=listing.id,
        abs=True,
        led_headlights=True
    )

    session.add_all([tech, equipment])
    await session.commit()

    license_key = LicenseKey(
        key="test-license-key",
        filters=[{
            "brand": "Audi",
            "technical_details": {"engine_type": "Elektro"},
            "equipment": {"abs": True}
        }]
    )

    listings = await get_filtered_for_ml(session, license_key)
    assert len(listings) == 1, f"Expected 1 listing, got {len(listings)}"
    assert isinstance(listings[0], ListingSchemaML), f"Expected ListingSchemaML instance, got {type(listings[0])}"
    assert listings[0].brand == "Audi", f"Expected brand 'Audi', got {listings[0].brand}"
    assert listings[
               0].technical_details.engine_type == "Elektro", "Expected engine_type 'Elektro', got {listings[0].technical_details.engine_type}"
    assert listings[0].equipment.abs is True, "Expected abs to be True, got {listings[0].equipment.abs}"


async def test_get_filtered(session):
    # Clean up the database before the test
    await session.execute(delete(TechnicalDetails))
    await session.execute(delete(Equipment))
    await session.execute(delete(ListingMobileDe))
    await session.commit()

    # Test data setup
    listing = ListingMobileDe(
        is_active=True,
        brand="Audi",
        model="A6",
        registration_year=2024,
        mileage=30000,
        city_or_postal_code="Berlin",
        color="Schwarz",
        price=45000,
        currency="EUR",
        url=f"https://example.com/audi-a6-{uuid.uuid4()}"
    )
    session.add(listing)
    await session.flush()  # needed listing.id

    equipment = Equipment(
        listing_id=listing.id,
        abs=True,
        adaptive_cruise_control=False
    )
    session.add(equipment)

    tech = TechnicalDetails(
        listing_id=listing.id,
        engine_type="Elektro",
        power=200
    )
    session.add(tech)

    await session.commit()

    # Prepare filters
    listing_filters = ListingSchema(brand="Audi")
    tech_filters = TechnicalDetailsSchema(engine_type="Elektro")
    equipment_filters = EquipmentSchema(abs=True)

    # ✅ call the function to test
    result: ListingFilteredResponse = await get_filtered(
        db=session,
        listing_filters=listing_filters,
        tech_filters=tech_filters,
        equipment_filters=equipment_filters,
        page=1, size=10, total=10
    )

    # Check results
    assert len(result.Listings) == 1
    assert result.Stats.count == 1
    assert result.Stats.min_price == 45000
    assert result.Stats.max_price == 45000
    assert result.Stats.avg_price == 45000

    listing_out = result.Listings[0]
    assert listing_out.brand == "Audi"
    assert listing_out.technical_details.engine_type == "Elektro"
    assert listing_out.equipment.abs is True
