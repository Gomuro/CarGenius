# app/services/stats/analytics.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from app.models.car import ListingMobileDe, Equipment, TechnicalDetails
from app.schemas.stats.analytics import AvgPriceByBrand, ListingSchema, TechnicalDetailsSchema, EquipmentSchema, \
    ListingCreateRequestSchema, ListingOut, ListingFilteredResponse, ListingStats
from app.services.stats.filter_mobilde import filtered_listings, filtered_tech_details, filtered_equipment


async def get_filterd(
        db: AsyncSession,
        listing_filters: ListingSchema,
        tech_filters: TechnicalDetailsSchema,
        equipment_filters: EquipmentSchema
) -> ListingFilteredResponse:
    """Filtering listings with JOIN on TechnicalDetails and Equipment."""
    listing_conditions = filtered_listings(listing_filters)
    techdetails_conditions = filtered_tech_details(tech_filters)
    equipment_conditions = filtered_equipment(equipment_filters)

    stmt = (
        select(ListingMobileDe)
        .outerjoin(ListingMobileDe.technical_details)
        .outerjoin(ListingMobileDe.equipment)
        .options(
            joinedload(ListingMobileDe.technical_details),
            joinedload(ListingMobileDe.equipment)
        )
        .where(and_(
            *listing_conditions,
            *techdetails_conditions,
            *equipment_conditions
        ))
    )
    result = await db.execute(stmt)

    listings = list(result.scalars().all())  # Return a list of ListingMobileDe objects
    listing_out = [ListingOut.from_orm(item) for item in listings]

    if listings:
        price_stmt = (
            select(
                func.avg(ListingMobileDe.price),
                func.min(ListingMobileDe.price),
                func.max(ListingMobileDe.price),
                func.count(ListingMobileDe.id)
            )
            .outerjoin(ListingMobileDe.technical_details)
            .outerjoin(ListingMobileDe.equipment)
            .where(and_(
                *listing_conditions,
                *techdetails_conditions,
                *equipment_conditions
            )))
        stats_result = await db.execute(price_stmt)
        avg_price, min_price, max_price, count = stats_result.one_or_none()  # return a single row (tuple)  with aggregated stats or None if no listings found
    else:
        avg_price = min_price = max_price = count = 0

    return ListingFilteredResponse(
        Listings=listing_out,
        Stats=ListingStats(
            avg_price=round(avg_price, 2) if avg_price else 0,
            min_price=round(min_price, 2) if min_price else 0,
            max_price=round(max_price, 2) if max_price else 0,
            count=count
        )
    )


async def listings_json_to_db(db: AsyncSession, data: ListingCreateRequestSchema) -> ListingMobileDe:
    """
    Save a listing to the database.
    """
    listing = ListingMobileDe(
        brand=data.brand,
        model=data.model,
        registration_year=data.registration_year,
        mileage=data.mileage,
        city_or_postal_code=data.city_or_postal_code,
        color=data.color,
        price=data.price,
        currency=data.currency,
        url=data.url,
    )

    technical_details = TechnicalDetails(
        **data.technical_details.dict() if data.technical_details else {})  # Show how to create TechnicalDetails from the schema
    equipment = Equipment(
        **data.equipment.dict() if data.equipment else {})  # Show how to create Equipment from the schema

    listing.technical_details = technical_details  # Add technical details to the listing
    listing.equipment = equipment  # Add equipment to the listing

    db.add(listing)  # Add the listing to the session
    await db.commit()  # Commit the session to save the listing
    await db.refresh(listing)  # Refresh the instance to get the updated state
    return listing


async def get_avg_price_by_brand(limit: int, db: AsyncSession) -> list[AvgPriceByBrand]:
    """
    Get average price, max price, min price, and count of car listings grouped by brand.
    """
    stmt = (
        select(
            ListingMobileDe.brand,
            func.avg(ListingMobileDe.price).label("avg_price"),
            func.min(ListingMobileDe.price).label("min_price"),
            func.max(ListingMobileDe.price).label("max_price"),
            func.count(ListingMobileDe.id).label("count")
        )
        .group_by(ListingMobileDe.brand)
        .order_by(func.avg(ListingMobileDe.price).desc())
        # .having(func.count(CarListingMobileDe.id) > 3)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        AvgPriceByBrand(
            brand=row.brand,
            avg_price=round(row.avg_price, 2),
            min_price=round(row.min_price, 2),
            max_price=round(row.max_price, 2),
            count=row.count
        )
        for row in rows
    ]
